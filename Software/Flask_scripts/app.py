import os
import shutil
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".txt"}
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)

def allowed(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def make_case_id():
    """Generate a unique case ID based on timestamp."""
    return datetime.now().strftime("case-%Y%m%d-%H%M%S-%f")

@app.route("/", methods=["GET"])
def index():
    return """
    <h1>Case Management Server</h1>
    <p>Available endpoints:</p>
    <ul>
        <li><b>POST /upload</b> – upload file (with optional case_id)</li>
        <li><b>GET /cases</b> – list all cases</li>
        <li><b>GET /cases/&lt;case_id&gt;</b> – list files in case</li>
        <li><b>GET /cases/&lt;case_id&gt;/&lt;filename&gt;</b> – view file inline</li>
        <li><b>GET /render/&lt;case_id&gt;</b> – render case in browser</li>
        <li><b>DELETE /purge/&lt;case_id&gt;</b> – delete entire case</li>
    </ul>
    """

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify(error="no file part"), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify(error="no selected file"), 400

    if not allowed(f.filename):
        return jsonify(error="only .jpg/.jpeg/.txt allowed"), 400

    # Case ID: provided or new
    case_id = request.form.get("case_id")
    if not case_id:
        case_id = make_case_id()

    case_dir = os.path.join(UPLOAD_DIR, case_id)
    os.makedirs(case_dir, exist_ok=True)

    # Save file with timestamp prefix to preserve order
    ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    safe = secure_filename(f.filename)
    name = f"{ts}-{safe}"
    path = os.path.join(case_dir, name)
    f.save(path)

    return jsonify({
        "ok": True,
        "case_id": case_id,
        "filename": name,
        "url": f"/cases/{case_id}/{name}"
    })

@app.route("/cases", methods=["GET"])
def list_cases():
    cases = [d for d in os.listdir(UPLOAD_DIR)
             if os.path.isdir(os.path.join(UPLOAD_DIR, d))]
    return jsonify(sorted(cases))

@app.route("/cases/<case_id>", methods=["GET"])
def list_case_files(case_id):
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    if not os.path.exists(case_dir):
        return jsonify(error="case not found"), 404
    return jsonify(sorted(os.listdir(case_dir)))

@app.route("/cases/<case_id>/<filename>", methods=["GET"])
def serve_case_file(case_id, filename):
    """Serve files inline instead of forcing download"""
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    if not os.path.exists(os.path.join(case_dir, filename)):
        abort(404)
    return send_from_directory(case_dir, filename, as_attachment=False)

@app.route("/render/<case_id>", methods=["GET"])
def render_case(case_id):
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    if not os.path.exists(case_dir):
        return f"<h1>Case {case_id} not found</h1>", 404

    # Sort files chronologically by filename (timestamp prefix)
    files = sorted(os.listdir(case_dir))

    cards = []
    for fname in files:
        filepath = os.path.join(case_dir, fname)
        if fname.lower().endswith((".jpg", ".jpeg")):
            # Show image
            cards.append(
                f"<div style='margin:10px;'><h3>{fname}</h3>"
                f"<img src='/cases/{case_id}/{fname}' style='max-width:400px;'></div>"
            )
        elif fname.lower().endswith(".txt"):
            # Show note inline
            with open(filepath, "r", encoding="utf-8") as f:
                preview = f.read()
            cards.append(
                f"<div style='margin:10px;'><h3>{fname}</h3>"
                f"<pre style='background:#f9f9f9;padding:10px;border:1px solid #ddd;'>{preview}</pre></div>"
            )
        else:
            # Other file → just a link
            cards.append(
                f"<div><h3>{fname}</h3><a href='/cases/{case_id}/{fname}'>Download</a></div>"
            )

    return f"<h1>Case {case_id}</h1>" + "".join(cards)

@app.route("/purge/<case_id>", methods=["DELETE"])
def purge_case(case_id):
    """Delete an entire case folder and its contents"""
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    if not os.path.exists(case_dir):
        return jsonify(error="case not found"), 404

    try:
        shutil.rmtree(case_dir)
        return jsonify({"ok": True, "message": f"Case {case_id} deleted"}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ------------------------------
# MAIN
# ------------------------------
if __name__ == "__main__":
    app.run(port=8000, debug=True)
