import os
import glob
import json

import pandas as pd
import numpy as np
from PIL import Image

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

from torchvision import transforms

from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (accuracy_score, f1_score, precision_recall_fscore_support)

from tqdm import tqdm

from models import (SkinCancerCNN, SkinCancerResNet, SkinCancerEfficientNet)


if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")


# Config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
METADATA_CSV = os.path.join(DATA_DIR, "HAM10000_metadata.csv")
IMAGE_DIRS = [
    os.path.join(DATA_DIR, "HAM10000_images_part_1"),
    os.path.join(DATA_DIR, "HAM10000_images_part_2")
]
MODELS_DIR = os.path.join(BASE_DIR, "models")

# The 7 HAM10000 diagnosis classes

LABELS = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
LABEL2IDX = {label: idx for idx, label in enumerate(LABELS)}

IMG_SIZE = 224
BATCH_SIZE = 32
NUM_WORKERS = 2
EPOCHS = 10
LR = 1e-4
VAL_SPLIT = 0.2
RANDOM_SEED = 42


# Dataset

class HAM10000Dataset(Dataset):
    def __init__(self, dataframe, transform=None):
        self.dataframe = dataframe.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        row = self.dataframe.iloc[idx]

        image = Image.open(row["image_path"]).convert("RGB")

        if self.transform is not None:
            image = self.transform(image)

        label = row["label_idx"]

        return image, label


def build_image_path_lookup(image_dirs):
    """Map image_id -> full file path by scanning both image folders once."""
    lookup = {}

    for image_dir in image_dirs:
        print(f"Scanning {image_dir} for images...")
        pattern = os.path.join(image_dir, "*.jpg")
        filepaths = glob.glob(pattern)
        print(f"  Found {len(filepaths)} images.")

        for filepath in tqdm(filepaths, desc=f"Indexing {os.path.basename(image_dir)}"):
            image_id = os.path.splitext(os.path.basename(filepath))[0]
            lookup[image_id] = filepath

    print(f"Total images indexed: {len(lookup)}")
    return lookup


def load_metadata():
    print(f"Reading metadata from {METADATA_CSV}...")
    df = pd.read_csv(METADATA_CSV)
    print(f"Metadata rows: {len(df)}")

    path_lookup = build_image_path_lookup(IMAGE_DIRS)

    df["image_path"] = df["image_id"].map(path_lookup)

    missing = df["image_path"].isna().sum()

    if missing > 0:
        print(f"Warning: {missing} images listed in metadata were not found on disk. Dropping them.")

        df = df.dropna(subset=["image_path"])

    df["label_idx"] = df["dx"].map(LABEL2IDX)

    print("Class distribution:")
    print(df["dx"].value_counts())

    return df


def get_transforms():
    # Standard ImageNet normalization
    # (matches ResNet18/EfficientNet pretrained weights)
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    )

    train_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        normalize,
    ])

    val_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        normalize,
    ])

    return train_transform, val_transform


def get_dataloaders():
    df = load_metadata()

    train_df, val_df = train_test_split(df, test_size=VAL_SPLIT, random_state=RANDOM_SEED, stratify=df["label_idx"])
    train_transform, val_transform = get_transforms()

    train_dataset = HAM10000Dataset(train_df, transform=train_transform)

    val_dataset = HAM10000Dataset(val_df, transform=val_transform)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS, pin_memory=(device.type == "cuda"))

    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE,shuffle=False, num_workers=NUM_WORKERS, pin_memory=(device.type == "cuda"))

    class_weights = compute_class_weight(class_weight="balanced", classes=np.arange(len(LABELS)), y=train_df["label_idx"].values)
    class_weights = torch.tensor(class_weights, dtype=torch.float32)

    return train_loader, val_loader, class_weights


# Training loop

def train_model(model, train_loader, val_loader, epochs=10, lr=1e-4, class_weights=None, device=None, save_path=os.path.join(MODELS_DIR, "best_model.pth")):
    if device is None:
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    model = model.to(device)

    if class_weights is not None:
        class_weights = class_weights.to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights)

    optimizer = optim.Adam(
        model.parameters(),
        lr=lr
    )

    best_val_acc = 0.0

    print(f"\nStarting training for {epochs} epochs on {device}.")

    for epoch in range(epochs):
        print(f"\n--- Epoch {epoch + 1}/{epochs} ---")

        model.train()

        running_loss = 0.0
        running_correct = 0
        running_total = 0

        train_bar = tqdm(
            train_loader,
            desc="Training",
            leave=False
        )

        for images, labels in train_bar:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            outputs = model(images)

            loss = criterion(outputs, labels)
            loss.backward()

            optimizer.step()

            running_loss += loss.item()

            predictions = outputs.argmax(dim=1)

            running_correct += (
                predictions == labels
            ).sum().item()
            running_total += labels.size(0)

            train_bar.set_postfix(loss=running_loss / (train_bar.n + 1), acc=running_correct / running_total)

        train_loss = running_loss / len(train_loader)
        train_acc = running_correct / running_total

        print(f"Training done. Loss: {train_loss:.4f} | Acc: {train_acc:.4f}.")
        print("Running validation...")

        model.eval()

        val_loss = 0.0
        val_correct = 0
        val_total = 0
        val_bar = tqdm(val_loader, desc="Validation", leave=False)

        with torch.no_grad():
            for images, labels in val_bar:
                images = images.to(device)
                labels = labels.to(device)

                outputs = model(images)

                loss = criterion(outputs, labels)
                val_loss += loss.item()

                predictions = outputs.argmax(dim=1)

                val_correct += (
                    predictions == labels
                ).sum().item()

                val_total += labels.size(0)

                val_bar.set_postfix(
                    loss=val_loss / (val_bar.n + 1),
                    acc=val_correct / val_total,
                )

        val_loss /= len(val_loader)
        val_acc = val_correct / val_total

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(
                model.state_dict(),
                save_path
            )
            print(
                f"New best model! Val Acc improved to "
                f"{val_acc:.4f} -> saved to {save_path}"
            )

        print(
            f"Epoch [{epoch + 1}/{epochs}] Summary | "
            f"Train Loss: {train_loss:.4f} "
            f"Train Acc: {train_acc:.4f} "
            f"Val Loss: {val_loss:.4f} "
            f"Val Acc: {val_acc:.4f}"
        )
    model.load_state_dict(torch.load(save_path, map_location=device))
    model.eval()

    all_labels = []
    all_predictions = []

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)

            outputs = model(images)

            predictions = outputs.argmax(dim=1)

            all_labels.extend(labels.cpu().numpy())
            all_predictions.extend(predictions.cpu().numpy())

    accuracy = accuracy_score(all_labels, all_predictions)

    f1 = f1_score(all_labels, all_predictions, average="weighted")

    precision, recall, _, _ = precision_recall_fscore_support(all_labels, all_predictions, labels=np.arange(len(LABELS)), zero_division=0)

    evaluations = {
        "accuracy": float(accuracy),
        "f1_score": float(f1),
        "per_class_precision": {
            LABELS[i]: float(precision[i])
            for i in range(len(LABELS))
        },
        "per_class_recall": {
            LABELS[i]: float(recall[i])
            for i in range(len(LABELS))
        },
    }

    json_path = os.path.splitext(save_path)[0] + ".json"

    with open(json_path, "w") as f:
        json.dump(evaluations, f, indent=4)

    print("\nFinal Evaluation:")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1 Score: {f1:.4f}")

    print("Per Class Precision:")

    for label in LABELS:
        print(f"  {label}: {evaluations['per_class_precision'][label]:.4f}"
        )
    print("Per Class Recall:")

    for label in LABELS:
        print(f"  {label}: {evaluations['per_class_recall'][label]:.4f}")

    print(f"Evaluation saved to: {json_path}")
    print(f"\nTraining complete. Best Validation Accuracy: {best_val_acc:.4f}")
    print(f"Best model saved to: {save_path}")

    return model


# Entry point

if __name__ == "__main__":
    print(f"Using device: {device}")
    print("Loading metadata and building dataloaders...")

    train_loader, val_loader, class_weights = get_dataloaders()

    print(f"Train batches: {len(train_loader)} | Val batches: {len(val_loader)}")
    print(f"Class weights: {class_weights}")

    models = [("cnn", SkinCancerCNN(num_classes=len(LABELS))),
            ("resnet", SkinCancerResNet(num_classes=len(LABELS))),
            ("efficientnet", SkinCancerEfficientNet(num_classes=len(LABELS))),
    ]

    for model_name, model in models:
        print(f"\nBuilding {model_name} model.")

        train_model(model, train_loader, val_loader, epochs=EPOCHS, lr=LR, class_weights=class_weights, device=device, save_path=os.path.join(MODELS_DIR, f"{model_name}_best.pth"))