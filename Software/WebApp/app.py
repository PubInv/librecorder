# ~/librecorder/Software/WebApp/app.py
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

# ----------------------------
# Path Configuration
# ----------------------------
base_dir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(base_dir, "uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".txt"}
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------------------------
# Flask App Initialization
# ----------------------------
app = Flask(
    __name__,
    template_folder=os.path.join(base_dir, "templates"),
    static_folder=os.path.join(base_dir, "static")
)
CORS(app)

# ----------------------------
# Database Setup
# ----------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(base_dir, 'openlims.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
with app.app_context():
    db.create_all()

queue_lock = threading.Lock()

# ----------------------------
# Utility Functions
# ----------------------------
def allowed(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def make_case_id():
    return datetime.now().strftime("case-%Y%m%d-%H%M%S-%f")

# ----------------------------
# Routes
# ----------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("dashboard.html")

@app.route("/upload_image", methods=["GET"])
def upload_image_page():
    """Render a browser-based image upload form."""
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload():
    with queue_lock:
        time.sleep(1)
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
import json

@app.route("/meta/<case_id>", methods=["GET", "POST"])
def case_meta(case_id):
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    if not os.path.exists(case_dir):
        return jsonify(error="case not found"), 404

    meta_path = os.path.join(case_dir, "meta.json")

    if request.method == "GET":
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
        # default meta if not present
        return jsonify({
            "domain": "health",
            "level": "Not Analyzed",          # Analyzed | Not Analyzed | Not for Analysis
            "columns": {},                   # analysis-type -> status (e.g., {"Microscopy QC":"Queued"})
            "tags": [],
            "notes": ""
        })

    # POST: save meta
    try:
        data = request.json or {}
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # keep DB description in sync if provided
        desc = data.get("description")
        if desc is not None:
            c = Case.query.filter_by(case_id=case_id).first()
            if c:
                c.description = desc
                db.session.commit()

        return jsonify(ok=True)
    except Exception as e:
        return jsonify(error=str(e)), 500

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
        return render_template("render_case.html", case_id=case_id, files=[], texts={}), 404

    files = sorted(os.listdir(case_dir))
    texts = {}
    for fname in files:
        if fname.lower().endswith(".txt"):
            try:
                with open(os.path.join(case_dir, fname), "r", encoding="utf-8") as f:
                    texts[fname] = f.read()
            except Exception:
                texts[fname] = "(unable to read file)"

    return render_template("render_case.html", case_id=case_id, files=files, texts=texts)

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

@app.route("/rich_results/<case_id>", methods=["GET"])
def rich_results(case_id):
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    if not os.path.exists(case_dir):
        return f"<h1>Case {case_id} not found</h1>", 404

    results = TestResult.query.filter_by(case_id=case_id).all()
    cards = []
    for fname in sorted(os.listdir(case_dir)):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        img_url = f"/cases/{case_id}/{fname}"
        overlay_items = [f"{r.test_name}: {r.result}" for r in results]
        overlay_html = ""
        if overlay_items:
            overlay_html = (
                "<div style='position:absolute;bottom:5px;left:5px;"
                "background:rgba(0,0,0,0.6);color:white;font-size:0.9em;"
                "padding:6px 8px;border-radius:4px;'>"
                + "<br>".join(overlay_items)
                + "</div>"
            )
        cards.append(
            f"<div style='position:relative;display:inline-block;margin:10px;'>"
            f"<img src='{img_url}' style='max-width:350px;border-radius:6px;"
            f"box-shadow:0 2px 8px rgba(0,0,0,0.3);'>{overlay_html}</div>"
        )
    html = f"""
    <html><head><title>Rich Results for {case_id}</title></head>
    <body style="font-family:sans-serif;background:#f8f8f8;text-align:center;">
      <h1>Rich Results for {case_id}</h1>
      <p><a href="/" style="font-weight:bold;">← Back to Dashboard</a></p>
      <div style="margin-top:20px;">{''.join(cards)}</div>
    </body></html>
    """
    return html

@app.route("/process", methods=["POST"])
def process_file():
    data = request.form
    case_id = data.get("case_id")
    filename = data.get("filename")
    processor = data.get("processor")

    if not case_id or not filename or not processor:
        return jsonify(error="Missing required fields"), 400

    file_path = os.path.join(UPLOAD_DIR, case_id, filename)
    if not os.path.exists(file_path):
        return jsonify(error="File not found"), 404

    try:
        proc_path = os.path.join(base_dir, "..", "processing", f"{processor}.py")
        spec = importlib.util.spec_from_file_location(processor, proc_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.run(file_path)

        tr = TestResult(case_id=case_id, test_name=processor, result=str(result), units="")
        db.session.add(tr)
        db.session.commit()

        return jsonify(result=result)
    except FileNotFoundError:
        return jsonify(error=f"Processor '{processor}' not found"), 404
    except Exception as e:
        return jsonify(error=str(e)), 500

# ----------------------------
# Entry Point
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
