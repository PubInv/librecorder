from PIL import Image
import numpy as np

def run(image_path):
    """Sigmoidal dark/light classifier."""
    img = Image.open(image_path).convert("L")
    arr = np.array(img)
    mean_val = np.mean(arr)

    # Sigmoid around 128 ±16
    sig_val = 1 / (1 + np.exp(-(mean_val - 128) / 16))
    label = "Dark" if sig_val < 0.5 else "Light"

    return {
        "sigmoid_score": round(float(sig_val), 3),
        "classification": label,
        "mean_val": round(float(mean_val), 2)
    }
