# ~/librecorder/Software/processing/mean_pixel.py
import numpy as np
from PIL import Image

MODEL_ID = "mean_pixel_v1"
MODEL_NAME = "Mean pixel value (v1)"
MODEL_TAGS = {
  "domain": "health",
  "task": "image_analysis",
  "expects.label_schema": "none",
  "expects.preproc_profile": "none",
  "compatible.specimen": "any",
  "compatible.modality": ["microscopy", "brightfield", "unknown"],
  "compatible.stain": "any",
  "compatible.magnification": "any"
}
def run(image_path):
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)
    mean_pixel = float(arr.mean())
    return {"mean_pixel": mean_pixel}
