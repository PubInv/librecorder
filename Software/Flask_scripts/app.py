# ~/librecorder/Software/Flask_scripts/app.py
import os
import shutil
import time
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, abort, render_template
from werkzeug.utils import secure_filename
import importlib.util
from flask_cors import CORS
from models import db, Case, TestResult

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".txt"}
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///openlims.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

queue_lock = threading.Lock()

def allowed(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def make_case_id():
    return datetime.now().strftime("case-%Y%m%d-%H%M%S-%f")

@app.route("/", methods=["GET"])
def index():
    return render_template("dashboard.html")

@app.route("/upload", methods=["POST"])
def upload():
    with queue_lock:
        time.sleep(2)
        if "file" not in request.files:
            return jsonify(error="no file part"), 400

        f = request.files["file"]
        if f.filename == "":
            return jsonify(error="no selected file"), 400

        if not allowed(f.filename):
            return jsonify(error="only .jpg/.jpeg/.txt allowed"), 400

        case_id = request.form.get("case_id") or make_case_id()
        case_dir = os.path.join(UPLOAD_DIR, case_id)
        os.makedirs(case_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        safe = secure_filename(f.filename)
        name = f"{ts}-{safe}"
        path = os.path.join(case_dir, name)
        f.save(path)

        # Log in database
        if not Case.query.filter_by(case_id=case_id).first():
            db.session.add(Case(case_id=case_id, description="Uploaded via API"))
            db.session.commit()

        return jsonify({
            "ok": True,
            "case_id": case_id,
            "filename": name,
            "url": f"/cases/{case_id}/{name}"
        })

@app.route("/cases", methods=["GET"])
def list_cases():
    cases = Case.query.all()
    return jsonify([
        {"case_id": c.case_id, "created_at": c.created_at.isoformat(), "description": c.description}
        for c in cases
    ])

@app.route("/cases/<case_id>", methods=["GET"])
def list_case_files(case_id):
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    if not os.path.exists(case_dir):
        return jsonify(error="case not found"), 404
    return jsonify(sorted(os.listdir(case_dir)))

@app.route("/cases/<case_id>/<filename>", methods=["GET"])
def serve_case_file(case_id, filename):
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    if not os.path.exists(os.path.join(case_dir, filename)):
        abort(404)
    return send_from_directory(case_dir, filename, as_attachment=False)

@app.route("/render/<case_id>", methods=["GET"])
def render_case(case_id):
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    if not os.path.exists(case_dir):
        return f"<h1>Case {case_id} not found</h1>", 404

    files = sorted(os.listdir(case_dir))
    cards = []

    for fname in files:
        filepath = os.path.join(case_dir, fname)
        if fname.lower().endswith((".jpg", ".jpeg")):
            cards.append(
                f"<div style='margin:10px;'><h3>{fname}</h3>"
                f"<img src='/cases/{case_id}/{fname}' style='max-width:400px;'></div>"
            )
        elif fname.lower().endswith(".txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                preview = f.read()
            cards.append(
                f"<div style='margin:10px;'><h3>{fname}</h3>"
                f"<pre style='background:#f9f9f9;padding:10px;border:1px solid #ddd;'>{preview}</pre></div>"
            )
        else:
            cards.append(
                f"<div><h3>{fname}</h3><a href='/cases/{case_id}/{fname}'>Download</a></div>"
            )

    return f"<h1>Case {case_id}</h1>" + "".join(cards)

@app.route("/purge/<case_id>", methods=["DELETE"])
def purge_case(case_id):
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    if not os.path.exists(case_dir):
        return jsonify(error="case not found"), 404
    try:
        shutil.rmtree(case_dir)
        Case.query.filter_by(case_id=case_id).delete()
        TestResult.query.filter_by(case_id=case_id).delete()
        db.session.commit()
        return jsonify({"ok": True, "message": f"Case {case_id} deleted"}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/record_result", methods=["POST"])
def record_result():
    data = request.json
    case_id = data.get("case_id")
    test_name = data.get("test_name")
    result = data.get("result")
    units = data.get("units", "")

    if not all([case_id, test_name, result]):
        return jsonify(error="Missing required fields"), 400

    if not Case.query.filter_by(case_id=case_id).first():
        return jsonify(error="Unknown case_id"), 404

    tr = TestResult(case_id=case_id, test_name=test_name, result=result, units=units)
    db.session.add(tr)
    db.session.commit()

    return jsonify(ok=True, message="Result logged successfully")

@app.route("/results/<case_id>", methods=["GET"])
def get_results(case_id):
    results = TestResult.query.filter_by(case_id=case_id).all()
    return jsonify([
        {"test_name": r.test_name, "result": r.result, "units": r.units, "timestamp": r.timestamp.isoformat()}
        for r in results
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
