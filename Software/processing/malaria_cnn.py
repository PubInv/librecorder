import os
import numpy as np
from PIL import Image

# Torch is heavy: only import once
import torch
import torch.nn as nn

MODEL_ID = "malaria_cnn_v1"
MODEL_NAME = "Malaria CNN (Infected vs Uninfected)"

# ---- model definition (copied from your predictMalaria.py) ----
class CNNModel(nn.Module):
    def __init__(self):
        super(CNNModel, self).__init__()
        self.conv1 = nn.Conv2d(3, 50, kernel_size=7, padding='same')
        self.conv2 = nn.Conv2d(50, 90, kernel_size=3, padding='valid')
        self.conv3 = nn.Conv2d(90, 10, kernel_size=5, padding='same')
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.conv4 = nn.Conv2d(10, 5, kernel_size=3, padding='same')
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.fc1 = nn.Linear(5 * 12 * 12, 2000)
        self.fc2 = nn.Linear(2000, 1000)
        self.fc3 = nn.Linear(1000, 500)
        self.fc4 = nn.Linear(500, 2)

        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.relu(self.conv3(x))
        x = self.pool1(x)

        x = self.relu(self.conv4(x))
        x = self.pool2(x)

        x = x.view(x.size(0), -1)

        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.relu(self.fc3(x))
        x = self.fc4(x)
        return x

# ---- lazy-loaded singleton ----
_MODEL = None
_DEVICE = None

def _find_checkpoint():
    """
    Expected location:
      ~/librecorder/Software/malaria_classifier/tmp/modelchkpt/bestmodel.pth
    This file is referenced relative to this processing/ directory.
    """
    here = os.path.abspath(os.path.dirname(__file__))
    ckpt = os.path.join(here, "..", "malaria_classifier", "tmp", "modelchkpt", "bestmodel.pth")
    ckpt = os.path.abspath(ckpt)
    if not os.path.exists(ckpt):
        raise FileNotFoundError(f"Malaria checkpoint not found at: {ckpt}")
    return ckpt

def _load_model():
    global _MODEL, _DEVICE
    if _MODEL is not None:
        return _MODEL

    _DEVICE = "cpu"
    ckpt_path = _find_checkpoint()

    checkpoint = torch.load(ckpt_path, map_location=_DEVICE)
    model = CNNModel()
    # your checkpoint format uses 'model_state_dict'
    sd = checkpoint["model_state_dict"] if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint else checkpoint
    model.load_state_dict(sd)
    model.eval()
    model.to(_DEVICE)

    _MODEL = model
    return _MODEL

def _preprocess(image_path):
    """
    Match your training/inference:
      - RGB
      - resize 50x50
      - normalize to [0,1]
      - tensor shape (1,3,50,50)
    """
    img = Image.open(image_path).convert("RGB").resize((50, 50))
    arr = np.array(img).astype("float32") / 255.0
    t = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)  # (1,C,H,W)
    return t

def run(image_path):
    model = _load_model()

    x = _preprocess(image_path)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]  # [p0, p1]

    # Label mapping consistent with your script:
    # 0 = Uninfected, 1 = Infected
    p_uninfected = float(probs[0])
    p_infected = float(probs[1])
    pred_idx = int(np.argmax(probs))
    classification = "Infected" if pred_idx == 1 else "Uninfected"
    confidence = float(probs[pred_idx])

    return {
        "classification": classification,
        "confidence": round(confidence, 6),
        "p_uninfected": round(p_uninfected, 6),
        "p_infected": round(p_infected, 6),
    }
