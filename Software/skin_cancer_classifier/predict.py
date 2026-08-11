import os
import argparse

from PIL import Image

import torch
from torchvision import transforms

from models import (
    SkinCancerCNN,
    SkinCancerResNet,
    SkinCancerEfficientNet,
)

LABELS = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]

IMG_SIZE = 224


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")


def get_transform():
    return transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        )])


def build_model(model_path, device):
    model_name = os.path.basename(model_path).lower()

    if "efficientnet" in model_name:
        model = SkinCancerEfficientNet(num_classes=len(LABELS))
    elif "resnet" in model_name:
        model = SkinCancerResNet(num_classes=len(LABELS))
    elif "cnn" in model_name:
        model = SkinCancerCNN(num_classes=len(LABELS))
    else:
        raise ValueError(f"Could not determine model architecture from the model filename: {model_path}. Model filename must contain 'cnn', 'resnet', or 'efficientnet'.")

    state_dict = torch.load(model_path, map_location=device)

    model.load_state_dict(state_dict)

    model = model.to(device)
    model.eval()

    return model


def predict(model_path, image_path):
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model does not exist: {model_path}")

    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image does not exist: {image_path}")

    device = get_device()

    print(f"Using device: {device}")
    print(f"Loading model: {model_path}")
    print(f"Loading image: {image_path}")

    model = build_model(model_path, device)

    transform = get_transform()

    image = Image.open(image_path).convert("RGB")

    image = transform(image)

    # Add batch dimension: [C, H, W] -> [1, C, H, W]
    image = image.unsqueeze(0)

    image = image.to(device)

    with torch.no_grad():
        outputs = model(image)

        probabilities = torch.softmax(outputs, dim=1)

        predicted_idx = probabilities.argmax(dim=1).item()

        confidence = probabilities[0, predicted_idx].item()

    predicted_label = LABELS[predicted_idx]

    print("\nPrediction:")
    print(f"  Class: {predicted_label}")
    print(f"  Confidence: {confidence:.4f}")

    print("\nClass Probabilities:")

    for i, label in enumerate(LABELS):
        print(f"  {label}: {probabilities[0, i].item():.4f}")

    return predicted_label, confidence


def main():
    parser = argparse.ArgumentParser(description="Run inference on a HAM10000 skin lesion image.")

    parser.add_argument("--model", required=True, help="Path to the trained .pth model.")

    parser.add_argument("--image", required=True, help="Path to the image to classify.")

    args = parser.parse_args()

    predict(model_path=args.model, image_path=args.image)


if __name__ == "__main__":
    main()