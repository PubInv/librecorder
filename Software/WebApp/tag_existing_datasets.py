#!/usr/bin/env python3
import os
import json
import shutil
from datetime import datetime

UPLOADS_DIR = "/home/ubuntu/librecorder/Software/WebApp/uploads"

# If your malaria dataset folder name does NOT contain "malaria",
# put the exact folder name(s) here.
EXPLICIT_MALARIA_DIRS = {
    # "case-20260217-230247-415329",
    # "your_malaria_folder_name_here",
}

COMMON = {
    "domain": "health",
    "modality": "microscopy",
    "preproc_profile": "raw-native",
    "level": "Not Analyzed",
    "columns": {},
    "notes": ""
}

DOG_TEMPLATE = {
    **COMMON,
    "task": "generic-image-analysis",
    "label_schema": "unlabeled",
    "specimen": "dog-cells",
    "stain": "unknown",
    "magnification": "unknown",
    "description": "Dog cell microscopy dataset",
    "tags": ["dog-cells", "microscopy", "darklight-ok", "meanpixel-ok"]
}

MALARIA_TEMPLATE = {
    **COMMON,
    "task": "classification",
    "label_schema": "infected-uninfected",
    "specimen": "blood",
    "stain": "giemsa",
    "magnification": "unknown",
    "description": "Malaria blood smear microscopy dataset",
    "tags": ["malaria", "blood-smear", "microscopy", "darklight-ok", "meanpixel-ok", "malaria-ok"]
}

OTHER_TEMPLATE = {
    **COMMON,
    "task": "generic-image-analysis",
    "label_schema": "unlabeled",
    "specimen": "cell",
    "stain": "unknown",
    "magnification": "unknown",
    "description": "Generic microscopy dataset",
    "tags": ["microscopy", "darklight-ok", "meanpixel-ok"]
}

STRUCTURED_KEYS = [
    "domain",
    "task",
    "label_schema",
    "preproc_profile",
    "specimen",
    "modality",
    "stain",
    "magnification",
    "level",
    "columns",
    "notes",
    "description",
    "tags"
]

def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def merge_tags(existing_tags, new_tags):
    existing_tags = existing_tags if isinstance(existing_tags, list) else []
    out = []
    for t in existing_tags + new_tags:
        if t not in out:
            out.append(t)
    return out

def classify_folder(folder_name):
    lower = folder_name.lower()

    if folder_name in EXPLICIT_MALARIA_DIRS:
        return "malaria"

    if "malaria" in lower:
        return "malaria"

    if folder_name.startswith("Dog_Cells_"):
        return "dog"

    return "other"

def template_for(kind):
    if kind == "malaria":
        return MALARIA_TEMPLATE
    if kind == "dog":
        return DOG_TEMPLATE
    return OTHER_TEMPLATE

def main():
    if not os.path.isdir(UPLOADS_DIR):
        raise RuntimeError(f"Uploads directory not found: {UPLOADS_DIR}")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    updated = []

    for name in sorted(os.listdir(UPLOADS_DIR)):
        folder = os.path.join(UPLOADS_DIR, name)
        if not os.path.isdir(folder):
            continue

        kind = classify_folder(name)
        template = template_for(kind)
        meta_path = os.path.join(folder, "meta.json")

        existing = load_json(meta_path)

        if os.path.exists(meta_path):
            backup_path = os.path.join(folder, f"meta.json.bak.{timestamp}")
            shutil.copy2(meta_path, backup_path)

        merged = dict(existing)

        # Overwrite the structured compatibility fields with the chosen template
        for k in STRUCTURED_KEYS:
            if k == "tags":
                merged["tags"] = merge_tags(existing.get("tags", []), template["tags"])
            elif k == "notes":
                merged["notes"] = existing.get("notes", template["notes"])
            elif k == "description":
                merged["description"] = existing.get("description") or template["description"]
            elif k == "columns":
                merged["columns"] = existing.get("columns", template["columns"])
            else:
                merged[k] = template[k]

        # Optional convenience field for humans/debugging
        merged["dataset_group"] = kind

        save_json(meta_path, merged)
        updated.append((name, kind, meta_path))

    print("\nUpdated datasets:\n")
    for name, kind, meta_path in updated:
        print(f"[{kind.upper():7}] {name} -> {meta_path}")

    print("\nDone.")
    print("\nIf your malaria dataset folder was not auto-detected, add it to EXPLICIT_MALARIA_DIRS and run again.")

if __name__ == "__main__":
    main()
