from __future__ import absolute_import, division, print_function

import random
import numpy as np # linear algebra
import cv2
import matplotlib.pyplot as plt
from PIL import Image
import os
import torch
from torch.utils.data import DataLoader, Dataset
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import time
import torch.nn as nn
###########################################INFERENCE#################################################################
class CNNModel(nn.Module):
    def __init__(self):
        super(CNNModel, self).__init__()

        # First conv block
        self.conv1 = nn.Conv2d(3, 50, kernel_size=7, padding='same')
        self.conv2 = nn.Conv2d(50, 90, kernel_size=3, padding='valid')
        self.conv3 = nn.Conv2d(90, 10, kernel_size=5, padding='same')
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Second conv block
        self.conv4 = nn.Conv2d(10, 5, kernel_size=3, padding='same')
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Fully connected layers
        # Calculate the size after convolutions and pooling
        # Input: 50x50x3
        # After conv2 (valid): 48x48
        # After pool1: 24x24
        # After pool2 (with padding): 12x12
        self.fc1 = nn.Linear(5 * 12 * 12, 2000)
        self.fc2 = nn.Linear(2000, 1000)
        self.fc3 = nn.Linear(1000, 500)
        self.fc4 = nn.Linear(500, 2)

        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        # First conv block
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.relu(self.conv3(x))
        x = self.pool1(x)

        # Second conv block
        x = self.relu(self.conv4(x))
        x = self.pool2(x)

        # Flatten
        x = x.view(x.size(0), -1)

        # Fully connected layers
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.relu(self.fc3(x))
        x = self.fc4(x)

        return x  # No softmax needed for CrossEntropyLoss
class TestMalariaDataset(Dataset):
    def __init__(self, image_paths, labels):
        self.image_paths = image_paths
        self.labels = labels

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        # Load image
        image = cv2.imread(self.image_paths[idx], cv2.IMREAD_UNCHANGED)
        image_array = Image.fromarray(image, 'RGB')
        resize_img = image_array.resize((50, 50))

        # Normalize to [0, 1]
        img_normalized = np.array(resize_img).astype('float32') / 255.0

        # Convert to tensor (C, H, W)
        img_tensor = torch.from_numpy(img_normalized).permute(2, 0, 1)

        label = self.labels[idx]
        path = self.image_paths[idx]
        return img_tensor, label,path
def visualize_predictions(image_paths, true_labels, predicted_classes, predictions, num_samples=10):
    """Visualize some test predictions"""

    # Get indices of correct and incorrect predictions
    correct_idx = np.where(predicted_classes == true_labels)[0]
    incorrect_idx = np.where(predicted_classes != true_labels)[0]

    # Show 5 correct and 5 incorrect (if available)
    num_correct = min(5, len(correct_idx))
    num_incorrect = min(5, len(incorrect_idx))

    fig, axes = plt.subplots(2, 5, figsize=(15, 6))

    # Show correct predictions
    for i in range(num_correct):
        idx = correct_idx[i]
        img = cv2.imread(image_paths[idx])
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (50, 50))

        ax = axes[0, i]
        ax.imshow(img)
        true_label = "Infected" if true_labels[idx] == 1 else "Uninfected"
        pred_label = "Infected" if predicted_classes[idx] == 1 else "Uninfected"
        confidence = predictions[idx][predicted_classes[idx]] * 100

        ax.set_title(f"✓ {true_label}\nConf: {confidence:.1f}%", color='green')
        ax.axis('off')

    # Fill empty slots
    for i in range(num_correct, 5):
        axes[0, i].axis('off')

    # Show incorrect predictions
    for i in range(num_incorrect):
        idx = incorrect_idx[i]
        img = cv2.imread(image_paths[idx])
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (50, 50))

        ax = axes[1, i]
        ax.imshow(img)
        true_label = "Infected" if true_labels[idx] == 1 else "Uninfected"
        pred_label = "Infected" if predicted_classes[idx] == 1 else "Uninfected"
        confidence = predictions[idx][predicted_classes[idx]] * 100

        ax.set_title(f"✗ True: {true_label}\nPred: {pred_label} ({confidence:.1f}%)",
                     color='red', fontsize=9)
        ax.axis('off')

    # Fill empty slots
    for i in range(num_incorrect, 5):
        axes[1, i].axis('off')

    axes[0, 0].text(-0.5, 0.5, 'CORRECT\nPREDICTIONS',
                    transform=axes[0, 0].transAxes,
                    fontsize=12, fontweight='bold',
                    va='center', ha='right', color='green')

    axes[1, 0].text(-0.5, 0.5, 'INCORRECT\nPREDICTIONS',
                    transform=axes[1, 0].transAxes,
                    fontsize=12, fontweight='bold',
                    va='center', ha='right', color='red')

    plt.tight_layout()
    plt.savefig('test_predictions.png', dpi=150, bbox_inches='tight')
    print("\n✓ Saved visualization to 'test_predictions.png'")
    plt.show()

# ===== CREATE TEST DATASET =====
print("Creating test dataset...")

infected = os.listdir('Data/Infected/')
uninfected = os.listdir('Data/Uninfected/')

# Sample 10 infected images
random.seed(42)  # For reproducibility
random_indices_inf = random.sample(range(len(infected)), 10)
infected_samples = [infected[i] for i in random_indices_inf]
infected_paths = [os.path.join('Data/Infected/', img) for img in infected_samples]
infected_labels = [1] * 10

# Sample 10 uninfected images
random_indices_uninf = random.sample(range(len(uninfected)), 10)
uninfected_samples = [uninfected[i] for i in random_indices_uninf]
uninfected_paths = [os.path.join('Data/Uninfected/', img) for img in uninfected_samples]
uninfected_labels = [0] * 10

# Combine both
test_image_paths = infected_paths + uninfected_paths
test_labels_list = infected_labels + uninfected_labels

# Shuffle the test set
combined = list(zip(test_image_paths, test_labels_list))
random.shuffle(combined)
test_image_paths, test_labels_list = zip(*combined)

print(f"✓ Created test dataset with {len(test_image_paths)} images")
print(f"  - Infected: {sum(test_labels_list)}")
print(f"  - Uninfected: {len(test_labels_list) - sum(test_labels_list)}")

# Create Dataset and DataLoader
test_dataset = TestMalariaDataset(test_image_paths, test_labels_list)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# ===== LOAD MODEL =====
print("\nLoading best model...")
checkpoint_dir = 'tmp/modelchkpt/'
checkpoint_path = os.path.join(checkpoint_dir, 'bestmodel.pth')

checkpoint = torch.load(checkpoint_path, map_location='cpu')
model = CNNModel()
model.load_state_dict(checkpoint['model_state_dict'])

# Move model to CPU for inference timing
model = model.cpu()
model.eval()
print(f"✓ Model's validation accuracy was: {checkpoint['val_accuracy']:.4f}")

# ===== RUN INFERENCE =====
all_predictions = []
all_probs = []
all_labels = []
all_paths = []
total_time = 0.0
num_images = 0

print("\n" + "=" * 60)
print("Running evaluation on CPU...")
print("=" * 60)

with torch.no_grad():
    for inputs, labels,paths in test_loader:
        inputs = inputs.cpu()  # Ensure on CPU

        # Time the inference
        start_time = time.perf_counter()
        outputs = model(inputs)
        end_time = time.perf_counter()

        # Accumulate time
        batch_time = end_time - start_time
        total_time += batch_time
        num_images += inputs.size(0)

        # Get predictions
        probs = torch.softmax(outputs, dim=1)
        _, predicted = torch.max(outputs, 1)

        all_predictions.extend(predicted.cpu().numpy())
        all_probs.extend(probs.cpu().numpy())
        all_labels.extend(labels.numpy())
        all_paths.extend(paths)

# Convert to numpy arrays
predictions = np.array(all_probs)
predicted_classes = np.array(all_predictions)
true_labels = np.array(all_labels)
image_paths_from_loader = all_paths
# ===== CALCULATE METRICS =====
accuracy = accuracy_score(true_labels, predicted_classes)
avg_time_per_image = (total_time / num_images) * 1000  # Convert to milliseconds

# ===== PRINT RESULTS =====
print("\n" + "=" * 60)
print("EVALUATION RESULTS:")
print("=" * 60)
print(f"Total images: {num_images}")
print(f"Accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")
print(f"Correct predictions: {(predicted_classes == true_labels).sum()}/{num_images}")
print(f"Total inference time: {total_time:.4f} seconds")
print(f"Average time per image: {avg_time_per_image:.2f} ms")
print(f"Images per second: {num_images / total_time:.2f}")

print("\n" + "=" * 60)
print("CONFUSION MATRIX:")
print("=" * 60)
cm = confusion_matrix(true_labels, predicted_classes)
print(cm)
print(f"\nTrue Negatives (Uninfected correctly identified):  {cm[0, 0]}")
print(f"False Positives (Uninfected predicted as Infected): {cm[0, 1]}")
print(f"False Negatives (Infected predicted as Uninfected): {cm[1, 0]}")
print(f"True Positives (Infected correctly identified):     {cm[1, 1]}")

# Calculate per-class accuracy
print(f"\nPer-class accuracy:")
print(f"  Uninfected: {cm[0, 0] / (cm[0, 0] + cm[0, 1]) * 100:.2f}%")
print(f"  Infected:   {cm[1, 1] / (cm[1, 0] + cm[1, 1]) * 100:.2f}%")

print("\n" + "=" * 60)
print("CLASSIFICATION REPORT:")
print("=" * 60)
print(classification_report(true_labels, predicted_classes,
                            target_names=['Uninfected', 'Infected']))

# Call the visualization function
visualize_predictions(image_paths_from_loader, true_labels, predicted_classes, predictions)