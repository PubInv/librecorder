# ~/librecorder/Software/WebApp/app.py
import os
import shutil
import time
import threading
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, abort, render_template
from werkzeug.utils import secure_filename
import importlib.util
from flask_cors import CORS
from models import db, Case, TestResult
from PIL import Image
import numpy as np
import glob
import requests

# ----------------------------
# Path Configuration
# ----------------------------
base_dir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(base_dir, "uploads")
TAG_REGISTRY_PATH = os.path.join(base_dir, "tag_registry.json")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".txt", ".png", ".tif", ".tiff"}
os.makedirs(UPLOAD_DIR, exist_ok=True)
SECRETS_PATH = os.path.join(base_dir, "secrets", "secrets.txt")

def load_runpod_secrets():
    out = {}
    if not os.path.exists(SECRETS_PATH):
        return out

    with open(SECRETS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out

_RUNPOD = load_runpod_secrets()
RUNPOD_ENDPOINT_ID = _RUNPOD.get("runpod_Endpoint_ID", "")
RUNPOD_API_KEY = _RUNPOD.get("runpod_api_key", "")
RUNPOD_RUNSYNC_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync" if RUNPOD_ENDPOINT_ID else ""

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
job_lock = threading.Lock()
RUN_JOBS = {}

# ----------------------------
# Tagging / Compatibility Rules
# ----------------------------
HARD_KEYS = ["domain", "task", "label_schema", "preproc_profile"]
SOFT_KEYS = ["specimen", "modality", "stain", "magnification"]


# ----------------------------
# Utility Functions
# ----------------------------
def allowed(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def make_case_id():
    return datetime.now().strftime("case-%Y%m%d-%H%M%S-%f")


def _as_set(v):
    if v is None:
        return set()
    if isinstance(v, list):
        return set(v)
    return {v}

def make_job_id():
    return datetime.now().strftime("job-%Y%m%d-%H%M%S-%f")


def json_safe(obj):
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)


def init_job(job_id, case_id, model_id, total_files):
    with job_lock:
        RUN_JOBS[job_id] = {
            "job_id": job_id,
            "case_id": case_id,
            "model_id": model_id,
            "status": "queued",   # queued, running, completed, failed
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "finished_at": None,
            "total_files": total_files,
            "completed_files": 0,
            "failed_files": 0,
            "progress_pct": 0,
            "current_file": None,
            "messages": [],
            "per_image": [],
            "aggregate": {},
            "error": None
        }


def update_job(job_id, **kwargs):
    with job_lock:
        if job_id in RUN_JOBS:
            RUN_JOBS[job_id].update(kwargs)


def append_job_message(job_id, message):
    with job_lock:
        if job_id in RUN_JOBS:
            RUN_JOBS[job_id]["messages"].append({
                "ts": datetime.now().isoformat(),
                "message": str(message)
            })


def append_job_result(job_id, item):
    with job_lock:
        if job_id in RUN_JOBS:
            RUN_JOBS[job_id]["per_image"].append(json_safe(item))
            completed = len(RUN_JOBS[job_id]["per_image"])
            total = max(1, RUN_JOBS[job_id]["total_files"])
            RUN_JOBS[job_id]["completed_files"] = completed
            RUN_JOBS[job_id]["progress_pct"] = int(round(100.0 * completed / total))

def normalize_dataset_tags(meta: dict):
    """
    Pull only the structured keys used by compatibility logic.
    Ignore freeform tags list for enforcement.
    """
    meta = meta or {}
    out = {}

    for k in HARD_KEYS + SOFT_KEYS:
        if k in meta:
            out[k] = meta.get(k)

    # domain is especially important, preserve if present even if emptyish
    if "domain" in meta and "domain" not in out:
        out["domain"] = meta.get("domain")

    return out


def load_case_meta(case_id: str):
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    meta_path = os.path.join(case_dir, "meta.json")
    if not os.path.exists(meta_path):
        return {}
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_model_module_by_id(model_id: str):
    proc_dir = os.path.join(base_dir, "..", "processing")

    for fname in sorted(os.listdir(proc_dir)):
        if not fname.endswith(".py"):
            continue
        if fname.startswith("_"):
            continue

        path = os.path.join(proc_dir, fname)
        name = os.path.splitext(fname)[0]

        try:
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            mid = str(getattr(mod, "MODEL_ID", name))
            if mid != model_id:
                continue

            return {
                "path": path,
                "name": name,
                "module": mod,
                "model_id": str(getattr(mod, "MODEL_ID", name)),
                "model_name": str(getattr(mod, "MODEL_NAME", name)),
                "model_tags": getattr(mod, "MODEL_TAGS", {})
            }
        except Exception:
            continue

    return None


def is_compatible(model_tags: dict, dataset_tags: dict):
    reasons = []

    model_tags = model_tags or {}
    dataset_tags = dataset_tags or {}

    # Hard requirements
    for k in HARD_KEYS:
        mv = model_tags.get(f"expects.{k}", model_tags.get(k))
        dv = dataset_tags.get(k)

        if mv is None:
            continue

        if dv is None:
            reasons.append(f"dataset missing required tag: {k}")
            continue

        if mv != dv:
            reasons.append(f"{k} mismatch (model expects {mv}, dataset has {dv})")

    # Soft constraints
    for k in SOFT_KEYS:
        allowed_vals = model_tags.get(f"compatible.{k}", "any")
        dv = dataset_tags.get(k)

        if allowed_vals == "any":
            continue

        if dv is None:
            reasons.append(f"dataset missing recommended tag: {k}")
            continue

        allowed_set = _as_set(allowed_vals)
        if dv not in allowed_set:
            reasons.append(
                f"{k} not allowed (dataset has {dv}, model allows {sorted(allowed_set)})"
            )

    return (len(reasons) == 0), reasons

@app.route("/api/tags", methods=["GET"])
def get_tags():
    return jsonify(load_tag_registry())


@app.route("/api/tags", methods=["POST"])
def create_tag():
    data = request.json or {}
    tag = (data.get("tag") or "").strip()

    if not tag:
        return jsonify(error="tag is required"), 400

    tags = load_tag_registry()
    lowered = {t.lower() for t in tags}
    if tag.lower() not in lowered:
        tags.append(tag)
        save_tag_registry(tags)

    return jsonify(ok=True, tag=tag, tags=load_tag_registry())


@app.route("/register_tag", methods=["GET"])
def register_tag_page():
    return render_template("register_tag.html")


def load_tag_registry():
    if not os.path.exists(TAG_REGISTRY_PATH):
        return []
    try:
        with open(TAG_REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def save_tag_registry(tags):
    tags = sorted(set(str(t).strip() for t in tags if str(t).strip()), key=str.lower)
    with open(TAG_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(tags, f, indent=2)


def merge_case_tags(case_id: str, tags_to_add):
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    meta_path = os.path.join(case_dir, "meta.json")

    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            meta = {}

    existing = meta.get("tags", [])
    if not isinstance(existing, list):
        existing = []

    merged = sorted(set(existing + [t for t in tags_to_add if t]), key=str.lower)
    meta["tags"] = merged

    if "domain" not in meta:
        meta["domain"] = "health"
    if "task" not in meta:
        meta["task"] = "image_analysis"
    if "label_schema" not in meta:
        meta["label_schema"] = "none"
    if "preproc_profile" not in meta:
        meta["preproc_profile"] = "none"
    if "specimen" not in meta:
        meta["specimen"] = "cell"
    if "modality" not in meta:
        meta["modality"] = "microscopy"
    if "stain" not in meta:
        meta["stain"] = "unknown"
    if "magnification" not in meta:
        meta["magnification"] = "unknown"

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

# ----------------------------
# Routes
# ----------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("dashboard.html")


@app.route("/upload_image", methods=["GET"])
def upload_image_page():
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
            return jsonify(error="unsupported file type"), 400

        case_id = request.form.get("case_id") or make_case_id()
        case_dir = os.path.join(UPLOAD_DIR, case_id)
        os.makedirs(case_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        safe = secure_filename(f.filename)
        name = f"{ts}-{safe}"
        path = os.path.join(case_dir, name)
        f.save(path)

        if not Case.query.filter_by(case_id=case_id).first():
            db.session.add(Case(case_id=case_id, description="Uploaded via API"))
            db.session.commit()

        return jsonify({
            "ok": True,
            "case_id": case_id,
            "filename": name,
            "url": f"/cases/{case_id}/{name}"
        })

        raw_tags = request.form.get("tags", "").strip()
        if raw_tags:
            parsed_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
            merge_case_tags(case_id, parsed_tags)

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

        return jsonify({
            "domain": "health",
            "task": "",
            "label_schema": "",
            "preproc_profile": "",
            "specimen": "",
            "modality": "",
            "stain": "",
            "magnification": "",
            "level": "Not Analyzed",
            "columns": {},
            "tags": [],
            "notes": "",
            "description": ""
        })

    try:
        data = request.json or {}
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

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


@app.route("/import_folder", methods=["POST"])
def import_folder():
    data = request.json or {}
    src = data.get("src")
    if not src or not os.path.isdir(src):
        return jsonify(error="src folder not found"), 400

    case_id = (data.get("case_id") or make_case_id()).strip()
    desc = (data.get("description") or f"Imported from {src}").strip()

    case_dir = os.path.join(UPLOAD_DIR, case_id)
    os.makedirs(case_dir, exist_ok=True)

    copied = 0
    for fname in sorted(os.listdir(src)):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
            continue
        src_path = os.path.join(src, fname)
        if not os.path.isfile(src_path):
            continue

        ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        safe = secure_filename(fname)
        dst_name = f"{ts}-{safe}"
        dst_path = os.path.join(case_dir, dst_name)
        shutil.copy2(src_path, dst_path)
        copied += 1

    if copied == 0:
        return jsonify(error="No image files copied from src"), 400

    if not Case.query.filter_by(case_id=case_id).first():
        db.session.add(Case(case_id=case_id, description=desc))
        db.session.commit()

    return jsonify(ok=True, case_id=case_id, copied=copied, description=desc)


@app.route("/models", methods=["GET"])
def list_models():
    proc_dir = os.path.join(base_dir, "..", "processing")
    files = sorted(glob.glob(os.path.join(proc_dir, "*.py")))

    out = []
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        if name.startswith("_"):
            continue

        try:
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            model_id = getattr(mod, "MODEL_ID", name)
            model_name = getattr(mod, "MODEL_NAME", name)

            if not hasattr(mod, "run"):
                continue

            tags = getattr(mod, "MODEL_TAGS", {})

            out.append({
                "id": str(model_id),
                "name": str(model_name),
                "file": os.path.basename(path),
                "tags": tags
            })
        except Exception:
            continue

    return jsonify(out)


@app.route("/compatibility", methods=["POST"])
def compatibility_check():
    data = request.json or {}
    case_id = (data.get("case_id") or "").strip()
    model_id = (data.get("model_id") or "").strip()

    if not case_id or not model_id:
        return jsonify(error="case_id and model_id are required"), 400

    c = Case.query.filter_by(case_id=case_id).first()
    if not c:
        return jsonify(error="Unknown case_id"), 404

    case_dir = os.path.join(UPLOAD_DIR, case_id)
    if not os.path.isdir(case_dir):
        return jsonify(error="case directory not found"), 404

    model_info = load_model_module_by_id(model_id)
    if not model_info:
        return jsonify(error=f"Unknown model_id: {model_id}"), 400

    raw_meta = load_case_meta(case_id)
    dataset_tags = normalize_dataset_tags(raw_meta)
    model_tags = model_info["model_tags"]

    ok, reasons = is_compatible(model_tags, dataset_tags)

    return jsonify({
        "ok": True,
        "compatible": ok,
        "reasons": reasons,
        "case_id": case_id,
        "model_id": model_id,
        "dataset_tags": dataset_tags,
        "model_tags": model_tags
    })


@app.route("/start_model_run", methods=["POST"])
def start_model_run():
    data = request.json or {}
    case_id = (data.get("case_id") or "").strip()
    model_id = (data.get("model_id") or "").strip()

    if not case_id or not model_id:
        return jsonify(error="case_id and model_id are required"), 400

    c = Case.query.filter_by(case_id=case_id).first()
    if not c:
        return jsonify(error="Unknown case_id"), 404

    case_dir = os.path.join(UPLOAD_DIR, case_id)
    if not os.path.isdir(case_dir):
        return jsonify(error="case directory not found"), 404

    model_info = load_model_module_by_id(model_id)
    if not model_info:
        return jsonify(error=f"Unknown model_id: {model_id}"), 400

    raw_meta = load_case_meta(case_id)
    dataset_tags = normalize_dataset_tags(raw_meta)
    model_tags = model_info["model_tags"]

    compatible, reasons = is_compatible(model_tags, dataset_tags)
    if not compatible:
        return jsonify({
            "ok": False,
            "error": "Dataset is not compatible with this model",
            "compatibility": {
                "compatible": False,
                "reasons": reasons
            },
            "dataset_tags": dataset_tags,
            "model_tags": model_tags
        }), 400

    img_files = [
        f for f in sorted(os.listdir(case_dir))
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff"))
    ]
    if not img_files:
        return jsonify(error="No images found in dataset"), 400

    job_id = make_job_id()
    init_job(job_id, case_id, model_id, len(img_files))

    t = threading.Thread(
        target=run_model_job,
        args=(job_id, case_id, model_id, request.host_url),
        daemon=True
    )
    t.start()

    return jsonify({
        "ok": True,
        "job_id": job_id,
        "redirect_url": f"/model_action/{job_id}"
    })

def run_model_via_runpod(model_id: str, image_url: str):
    if not RUNPOD_ENDPOINT_ID or not RUNPOD_API_KEY:
        raise RuntimeError("RunPod secrets are not configured")

    payload = {
        "input": {
            "model_id": model_id,
            "image_url": image_url
        }
    }

    r = requests.post(
        RUNPOD_RUNSYNC_URL,
        headers={
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    r.raise_for_status()

    data = r.json()
    if data.get("status") != "COMPLETED":
        raise RuntimeError(f"RunPod job did not complete: {data}")

    return data.get("output", {})

def run_model_job(job_id, case_id, model_id, host_url):
    try:
        update_job(
            job_id,
            status="running",
            started_at=datetime.now().isoformat()
        )

        case_dir = os.path.join(UPLOAD_DIR, case_id)
        raw_meta = load_case_meta(case_id)
        dataset_tags = normalize_dataset_tags(raw_meta)

        model_info = load_model_module_by_id(model_id)
        if not model_info:
            raise RuntimeError(f"Unknown model_id: {model_id}")

        model_tags = model_info["model_tags"]
        compatible, reasons = is_compatible(model_tags, dataset_tags)
        if not compatible:
            raise RuntimeError("Dataset is not compatible with this model: " + "; ".join(reasons))

        img_files = [
            f for f in sorted(os.listdir(case_dir))
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff"))
        ]
        if not img_files:
            raise RuntimeError("No images found in dataset")

        per_image = []

        for idx, fname in enumerate(img_files, start=1):
            update_job(job_id, current_file=fname)
            append_job_message(job_id, f"Running {fname} ({idx}/{len(img_files)})")

            try:
                image_url = host_url.rstrip("/") + f"/cases/{case_id}/{fname}"
                result = run_model_via_runpod(model_id, image_url)

                item = {
                    "file": fname,
                    "result": json_safe(result)
                }
                per_image.append(item)
                append_job_result(job_id, item)
                append_job_message(job_id, f"Completed {fname}")

            except Exception as e:
                item = {
                    "file": fname,
                    "error": str(e)
                }
                per_image.append(item)
                append_job_result(job_id, item)

                with job_lock:
                    RUN_JOBS[job_id]["failed_files"] += 1

                append_job_message(job_id, f"Failed {fname}: {e}")

        agg = {}

        vals = [
            x["result"]["mean_pixel"]
            for x in per_image
            if "result" in x and isinstance(x["result"], dict) and "mean_pixel" in x["result"]
        ]
        if vals:
            avg = sum(float(v) for v in vals) / len(vals)
            agg["mean_pixel_avg"] = round(avg, 4)

        classes = [
            x["result"]["classification"]
            for x in per_image
            if "result" in x and isinstance(x["result"], dict) and "classification" in x["result"]
        ]
        if classes:
            counts = {}
            for k in classes:
                counts[k] = counts.get(k, 0) + 1
            agg["class_counts"] = counts

        tr = TestResult(
            case_id=case_id,
            test_name=f"model:{model_id}",
            result=json.dumps(agg if agg else {"ran": len(per_image)}),
            units=""
        )
        db.session.add(tr)
        db.session.commit()

        update_job(
            job_id,
            status="completed",
            finished_at=datetime.now().isoformat(),
            current_file=None,
            aggregate=json_safe(agg),
            progress_pct=100
        )
        append_job_message(job_id, "Job completed")

    except Exception as e:
        update_job(
            job_id,
            status="failed",
            finished_at=datetime.now().isoformat(),
            current_file=None,
            error=str(e)
        )
        append_job_message(job_id, f"Job failed: {e}")

@app.route("/job_status/<job_id>", methods=["GET"])
def job_status(job_id):
    with job_lock:
        job = RUN_JOBS.get(job_id)

    if not job:
        return jsonify(error="job not found"), 404

    return jsonify(job)


@app.route("/model_action/<job_id>", methods=["GET"])
def model_action_page(job_id):
    return render_template("model_action.html", job_id=job_id)


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
    app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)
