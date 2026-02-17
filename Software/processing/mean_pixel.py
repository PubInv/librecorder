# ~/librecorder/Software/processing/mean_pixel.py
import numpy as np
from PIL import Image

MODEL_ID = "mean_pixel_v1"
MODEL_NAME = "Mean pixel value (v1)"

def run(image_path):
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)
    mean_pixel = float(arr.mean())
    return {"mean_pixel": mean_pixel}
