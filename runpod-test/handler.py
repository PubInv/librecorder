import runpod
import requests
from io import BytesIO
from PIL import Image
import numpy as np


def mean_pixel(image):
    arr = np.array(image.convert("RGB"), dtype=np.float32)
    return {
        "source": "runpod",
        "mean_pixel": round(float(arr.mean()), 6)
    }


def dark_light(image):
    arr = np.array(image.convert("L"), dtype=np.float32)
    mean_val = float(arr.mean())
    sig_val = 1.0 / (1.0 + np.exp(-(mean_val - 128.0) / 16.0))
    label = "Dark" if sig_val < 0.5 else "Light"

    return {
        "source": "runpod",
        "sigmoid_score": round(float(sig_val), 6),
        "classification": label,
        "mean_val": round(mean_val, 6),
        "units": ""
    }


def handler(job):
    input_data = job.get("input", {})
    model_id = input_data.get("model_id")
    image_url = input_data.get("image_url")

    if not model_id:
        return {"source": "runpod", "error": "missing model_id"}
    if not image_url:
        return {"source": "runpod", "error": "missing image_url"}

    r = requests.get(image_url, timeout=60)
    r.raise_for_status()

    image = Image.open(BytesIO(r.content))

    if model_id == "mean_pixel_v1":
        return mean_pixel(image)

    if model_id == "dark_light_v1":
        return dark_light(image)

    return {
        "source": "runpod",
        "error": f"unsupported model_id: {model_id}"
    }


runpod.serverless.start({"handler": handler})
