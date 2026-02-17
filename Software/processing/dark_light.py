from PIL import Image
import numpy as np

MODEL_ID = "dark_light_v1"
MODEL_NAME = "Dark/Light (sigmoid)"

def run(image_path: str):
    """Sigmoidal dark/light classifier for one image."""
    img = Image.open(image_path).convert("L")
    arr = np.array(img, dtype=np.float32)
    mean_val = float(np.mean(arr))

    sig_val = 1 / (1 + np.exp(-(mean_val - 128.0) / 16.0))
    label = "Dark" if sig_val < 0.5 else "Light"

    return {
        "sigmoid_score": round(float(sig_val), 3),
        "classification": label,
        "mean_val": round(mean_val, 2),
        "units": ""
    }
