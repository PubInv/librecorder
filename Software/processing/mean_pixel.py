import numpy as np
from PIL import Image
import sys

def process(image_path):
    """Demonstrate image processing capability by computing the mean pixel value."""
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)
    mean_pixel = arr.mean()
    print(f"Mean pixel value: {mean_pixel}")
    return {"mean_pixel": float(mean_pixel)}

## CLI option
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python simple_processing.py <image_path>")
        sys.exit(1)
    process(sys.argv[1])