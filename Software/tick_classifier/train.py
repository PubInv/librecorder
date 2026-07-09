import numpy as np
import pandas as pd
from pathlib import Path

from tqdm import tqdm

import torch
import torch.nn.functional as F
from torchvision import transforms
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader
from torch import optim, nn


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

DATA_DIR = Path(__file__).parent / "data"

BATCH_SIZE = 32
LEARNING_RATE = 1e-3
NUM_EPOCHS = 10


class CNN(nn.Module):

    def __init__(self, in_channels=3, num_classes=2):

        super(CNN, self).__init__()

        self.conv1 = nn.Conv2d(in_channels, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)

        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))

        self.fc = nn.Linear(64, num_classes)

    def forward(self, x):

        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))

        x = self.avgpool(x)

        x = torch.flatten(x, 1)

        x = self.fc(x)

        return x


def create_dataloaders(batch_size):

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor()
    ])

    train_dataset = ImageFolder(
        root=DATA_DIR / "train",
        transform=transform
    )

    test_dataset = ImageFolder(
        root=DATA_DIR / "test",
        transform=transform
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=2,
        pin_memory=torch.cuda.is_available()
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory=torch.cuda.is_available()
    )

    return train_loader, test_loader


def train_model(model, train_loader, criterion, optimizer, epochs):

    for epoch in range(epochs):

        model.train()

        running_loss = 0
        correct = 0
        total = 0

        progress = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")

        for images, labels in progress:

            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            outputs = model(images)

            loss = criterion(outputs, labels)
            loss.backward()

            optimizer.step()

            running_loss += loss.item()

            predictions = torch.argmax(outputs, dim=1)

            correct += (predictions == labels).sum().item()
            total += labels.size(0)

            progress.set_postfix(
                loss=f"{loss.item():.4f}",
                acc=f"{100 * correct / total:.2f}%"
            )


def evaluate_model(model, test_loader, criterion):

    model.eval()

    correct = 0
    total = 0
    loss_total = 0

    progress = tqdm(
        test_loader,
        total=len(test_loader),
        desc="Evaluating",
        leave=True
    )

    with torch.no_grad():

        for images, labels in progress:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = criterion(outputs, labels)
            loss_total += loss.item()

            predictions = torch.argmax(outputs, dim=1)

            correct += (predictions == labels).sum().item()
            total += labels.size(0)

            progress.set_postfix({
                "loss": f"{loss.item():.4f}",
                "acc": f"{100 * correct / total:.2f}%"
            })


    accuracy = 100 * correct / total
    loss = loss_total / len(test_loader)

    print(f"""\nTest Loss: {loss:.4f}\n
            Test Accuracy: {accuracy:.2f}%
        """)

    return accuracy

if __name__ == "__main__":
    
    train_loader, test_loader = create_dataloaders(BATCH_SIZE)

    model = CNN(in_channels=3, num_classes=2).to(device)

    criterion = nn.CrossEntropyLoss()

    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    train_model(model, train_loader, criterion, optimizer, NUM_EPOCHS)

    evaluate_model(model, test_loader, criterion)
