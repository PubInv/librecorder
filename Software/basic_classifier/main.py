import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay


data_dir = "./"  
classes = ["cardiac", "stomach", "tongue2", "urinary2"]


def extract_features(img):
    """
    Input: img as a NumPy array (RGB)
    Output: mean R, G, B values
    """
    mean_rgb = img.mean(axis=(0, 1))  
    return mean_rgb #avg RGB(mean R, mean G, mean B)


class_means = {
    0: np.array([180, 50, 50]),    # cardiac
    1: np.array([160, 120, 100]),  # stomach
    2: np.array([200, 60, 70]),    # tongue2
    3: np.array([220, 200, 150])   # urinary2
}

def classify_feature(mean_rgb):
    """
    Classify image by comparing mean RGB to class prototypes.
    """
    distances = [np.linalg.norm(mean_rgb - class_means[i]) for i in range(4)]
    return int(np.argmin(distances))  # class with smallest distance


true_labels = []
predicted_labels = []

for class_index, class_name in enumerate(classes):
    folder_path = os.path.join(data_dir, class_name)

    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        continue

    for file in os.listdir(folder_path):
        if file.lower().endswith((".jpg", ".jpeg", ".png")):
            img_path = os.path.join(folder_path, file)
            img = cv2.imread(img_path)

            if img is None:
                print("Failed to load:", img_path)
                continue

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            features = extract_features(img_rgb)
            pred_label = classify_feature(features)

            true_labels.append(class_index)
            predicted_labels.append(pred_label)

# -----------------------
# Step 5: Confusion matrix
# -----------------------
cm = confusion_matrix(true_labels, predicted_labels)
disp = ConfusionMatrixDisplay(cm, display_labels=classes)
disp.plot(cmap="viridis")
plt.title("Confusion Matrix (Improved RGB Classifier)")
plt.show()
