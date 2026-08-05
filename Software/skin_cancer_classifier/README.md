# HAM10000 Skin-Lesion Classification

This project implements a seven-class convolutional neural network for the Skin Cancer MNIST: HAM10000 dataset using TensorFlow and Keras.

## Classes

The classifier predicts one of seven HAM10000 class codes:

| Code    | Description                                   |
| ------- | --------------------------------------------- |
| `akiec` | Actinic keratoses / intraepithelial carcinoma |
| `bcc`   | Basal cell carcinoma                          |
| `bkl`   | Benign keratosis-like lesions                 |
| `df`    | Dermatofibroma                                |
| `mel`   | Melanoma                                      |
| `nv`    | Melanocytic nevi                              |
| `vasc`  | Vascular lesions                              |

## Project workflow

```
HAM10000 metadata and JPG images
        ↓
Dataset validation and exploration
        ↓
Image-to-metadata mapping
        ↓
Lesion-level train/validation/test split
        ↓
TensorFlow image preprocessing
        ↓
Training-only data augmentation
        ↓
Class-weighted custom CNN
        ↓
Evaluation on unseen test images
        ↓
Command-line and Streamlit prediction
```

## Important data-splitting decision

HAM10000 can contain multiple images of the same lesion. The dataset is therefore split using `lesion_id`, not only individual image IDs.

This prevents images of the same lesion from appearing in both training and testing.

The generated split is approximately:

```text
64% training
16% validation
20% testing
```

Exact percentages may differ because lesions are kept together.

## Folder structure

```text
skin_cancer_classifier/
├── artifacts/
├── data/
│   ├── raw/
│   └── splits/
├── reports/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── data_pipeline.py
│   ├── evaluate.py
│   ├── explore_data.py
│   ├── model.py
│   ├── predict.py
│   ├── prepare_data.py
│   └── train.py
├── .gitignore
├── check_setup.py
├── requirements.txt
├
└── streamlit_app.py
```

## Dataset

Download the Skin Cancer MNIST: HAM10000 dataset from Kaggle.

Only these three items are needed:

```
HAM10000_images_part_1/
HAM10000_images_part_2/
HAM10000_metadata.csv
```

Place them here:

```
data/raw/
├── HAM10000_images_part_1/
├── HAM10000_images_part_2/
└── HAM10000_metadata.csv
```

The alternate `hmnist_8_8` and `hmnist_28_28` CSV files are not used by this implementation.

The raw dataset is excluded from Git and must be downloaded separately.

## Windows installation

Python 3.11 is recommended.

Create a virtual environment:

```powershell
py -3.11 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Verify TensorFlow:

```powershell
python check_setup.py
```

A successful output ends with:

```text
TensorFlow installation is working.
```

Current TensorFlow versions use the CPU on native Windows. WSL2 or Google Colab can be used for GPU training.

## Dataset exploration

Run:

```powershell
python -m src.explore_data
```

Important expected output:

```text
Number of images found: 10015
Images referenced in metadata but not found: 0
```

Generated reports:

```text
reports/class_distribution.png
reports/sample_images.png
```

## Dataset preprocessing

Run:

```powershell
python -m src.prepare_data
```

This operation:

1. Loads `HAM10000_metadata.csv`.
2. Validates `image_id`, `lesion_id` and `dx`.
3. Finds all JPG images in the two image folders.
4. Connects image IDs to their image paths.
5. Creates numeric labels.
6. Splits the dataset by `lesion_id`.
7. Creates training, validation and test CSV files.
8. Confirms that no lesion occurs in multiple splits.

Important expected output:

```text
Confirmed: no lesion_id appears in more than one split.
```

Generated files:

```text
data/splits/train.csv
data/splits/val.csv
data/splits/test.csv
```

## Image preprocessing

Each image is:

1. Read as an RGB image.
2. Resized with padding to `128 × 128`.
3. Converted to `float32`.
4. Batched using TensorFlow.
5. Normalized from `0–255` to `0–1` inside the model.

Training images also receive random:

* Horizontal and vertical flips
* Rotation
* Zoom
* Translation
* Contrast adjustment

Augmentation is not applied to validation, testing or prediction images.

## CNN architecture

The baseline CNN contains:

* Four convolution blocks
* Batch normalization
* ReLU activation
* Max pooling
* Dropout
* Global average pooling
* Dense classification layer
* Seven-class Softmax output

Class weights are calculated from the training set to reduce the effect of class imbalance.

## Smoke-test training

Before full training, run:

```powershell
python -m src.train --epochs 2
```

This verifies that the complete pipeline works.

Expected generated files:

```text
artifacts/best_model.keras
artifacts/training_log.csv
reports/training_accuracy.png
reports/training_loss.png
```

## Full training

Run:

```powershell
python -m src.train --epochs 30
```

The training process uses:

* Adam optimizer
* Sparse categorical cross-entropy
* Class weights
* Model checkpointing
* Early stopping
* Learning-rate reduction
* CSV logging

Training may stop before 30 epochs if validation loss stops improving.

## Evaluation

Run:

```powershell
python -m src.evaluate
```

Generated reports:

```text
reports/classification_report.txt
reports/classification_report.csv
reports/per_class_metrics.csv
reports/confusion_matrix.png
reports/test_metrics.json
reports/test_predictions.csv
```

Reported metrics include:

* Accuracy
* Balanced accuracy
* Macro F1
* Weighted F1
* Multiclass ROC-AUC
* Per-class precision
* Per-class sensitivity/recall
* Per-class specificity
* Per-class F1-score
* Confusion matrix

## Predict one image

Run:

```powershell
python -m src.predict --image "C:\full\path\to\image.jpg"
```

Example:

```powershell
python -m src.predict --image "$HOME\Downloads\Actinic Keratosis.jpg"
```

Expected output format:

```json
{
  "predicted_class": "akiec",
  "description": "Actinic keratoses / intraepithelial carcinoma",
  "confidence": 0.0,
  "probabilities": {
    "akiec": 0.0,
    "bcc": 0.0,
    "bkl": 0.0,
    "df": 0.0,
    "mel": 0.0,
    "nv": 0.0,
    "vasc": 0.0
  }
}
```

The actual class and probability values depend on the trained model.

## Streamlit demonstration

Start the upload interface:

```powershell
python -m streamlit run streamlit_app.py
```

Open:

```text
http://localhost:8501
```

Upload a JPG, JPEG or PNG image.

The application displays:

* Uploaded image
* Predicted class code
* Full class description
* Confidence
* All seven class probabilities
* Probability bar chart

## Known limitations

1. The model is a research proof of concept and is not clinically validated.
2. It has been evaluated only on a held-out portion of HAM10000.
3. It has not been externally validated on images from another hospital, camera or population.
4. HAM10000 is highly imbalanced, even though class weighting is used.
5. Minority-class sensitivity may remain substantially lower than overall accuracy.
6. The custom CNN may perform worse than pretrained architectures such as EfficientNet or ResNet.
7. Predictions and confidence values may be incorrect or poorly calibrated.
8. The model currently uses only image pixels and does not use age, sex, localization or other metadata.
9. Native Windows training is CPU-only for current TensorFlow versions and may be slow.
10. The classifier is not yet connected directly to the Librecorder WebApp or processing-module interface.
11. The raw dataset is not included in GitHub because of its size and licensing requirements.
12. The trained `.keras` model is not included in ordinary Git unless distributed separately through an approved model-storage method.

## Recommended next steps

1. Compare the custom CNN with EfficientNetB0 or ResNet transfer learning.
2. Evaluate focal loss and alternative class-balancing methods.
3. Tune image size, learning rate, batch size and dropout.
4. Add confidence calibration and an uncertainty threshold.
5. Perform external validation.
6. Add Grad-CAM visualizations for model inspection.
7. Create a Librecorder-compatible processing wrapper.

