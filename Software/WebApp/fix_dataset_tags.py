import os, json

UPLOADS = "/home/ubuntu/librecorder/Software/WebApp/uploads"

def write_meta(folder, meta):
    path = os.path.join(folder, "meta.json")
    with open(path, "w") as f:
        json.dump(meta, f, indent=2)

for name in os.listdir(UPLOADS):

    path = os.path.join(UPLOADS, name)
    if not os.path.isdir(path):
        continue

    if name.startswith("Dog_Cells"):
        meta = {
            "domain":"health",
            "task":"image_analysis",
            "label_schema":"none",
            "preproc_profile":"none",
            "specimen":"dog_cells",
            "modality":"microscopy",
            "stain":"unknown",
            "magnification":"unknown"
        }

    elif "malaria" in name.lower():

        meta = {
            "domain":"health",
            "task":"classification",
            "label_schema":"infected-uninfected",
            "preproc_profile":"rgb",
            "specimen":"blood",
            "modality":"microscopy",
            "stain":"giemsa",
            "magnification":"100x"
        }

    else:

        meta = {
            "domain":"health",
            "task":"image_analysis",
            "label_schema":"none",
            "preproc_profile":"none",
            "specimen":"cell",
            "modality":"microscopy",
            "stain":"unknown",
            "magnification":"unknown"
        }

    write_meta(path, meta)

print("Dataset tags fixed.")

