# HAM10000 Skin Cancer Classification

This project trains and evaluates three image classification models on the HAM10000 skin lesion dataset. The goal is to classify dermatoscopic images into one of seven different skin lesion categories.

## Dataset

HAM10000 contains 10,015 dermatoscopic images across seven diagnostic categories.

### Classes

| Label     | Diagnosis                                     | Number of Images | Definition                                                                                                                                             |
| --------- | --------------------------------------------- | ---------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `akiec`   | Actinic keratoses / intraepithelial carcinoma |              327 | Precancerous skin lesions caused by long-term sun exposure that can potentially progress to squamous cell carcinoma.                                   |
| `bcc`     | Basal cell carcinoma                          |              514 | A common form of skin cancer originating from basal cells. It generally grows slowly and rarely spreads to other parts of the body.                    |
| `bkl`     | Benign keratosis-like lesions                 |            1,099 | Benign skin lesions including seborrheic keratoses, solar lentigines, and other keratosis-like lesions.                                                |
| `df`      | Dermatofibroma                                |              115 | A common benign skin growth composed primarily of fibrous tissue.                                                                                      |
| `mel`     | Melanoma                                      |            1,113 | A malignant skin cancer originating from melanocytes. It can spread to other parts of the body and is the most serious of the classes in this dataset. |
| `nv`      | Melanocytic nevi                              |            6,705 | Commonly known as moles. These are generally benign growths of melanocytes.                                                                            |
| `vasc`    | Vascular lesions                              |              142 | Lesions involving blood vessels, including conditions such as angiomas and other vascular growths.                                                     |
| Total |                                               |       10,015 |                                                                                                                                                        |

### Dataset Characteristics

The dataset has significant class imbalance. For example, there are 6,705 `nv` images but only 115 `df` images.

To account for this imbalance, the training pipeline uses class-weighted cross-entropy loss so that less frequent classes have a larger influence during training.

The images are:

* Converted to RGB
* Resized to 224 × 224 pixels
* Normalized using ImageNet mean and standard deviation

Training images also use:

* Random horizontal flipping
* Random rotation up to 15 degrees

The dataset is split into:

| Dataset    | Percentage |
| ---------- | ---------: |
| Training   |        80% |
| Validation |        20% |


## Models

Three different CNN architectures are trained and evaluated.

### Custom CNN

A custom convolutional neural network consisting of four convolutional layers followed by adaptive average pooling and fully connected classification layers.

### ResNet18

A pretrained ResNet18 model using ImageNet weights. The final fully connected layer is replaced with a seven-class classification layer.

### EfficientNet-B0

A pretrained EfficientNet-B0 model using ImageNet weights. The final classification layer is replaced with a seven-class classification layer.

## Model Evaluation

### Overall Performance

| Model               |   Accuracy |   F1 Score |
| ------------------- | ---------: | ---------: |
| Custom CNN          |     52.87% |     57.00% |
| ResNet18            |     84.07% |     84.65% |
| EfficientNet-B0 | 84.52% | 85.22%|

EfficientNet-B0 performed the best overall, followed closely by ResNet18. Both pretrained models performed significantly better than the custom CNN.

### Custom CNN

| Class   | Precision | Recall |
| ------- | --------: | -----: |
| `akiec` |    17.98% | 24.62% |
| `bcc`   |    21.21% | 61.17% |
| `bkl`   |    25.40% | 35.91% |
| `df`    |    25.00% | 13.04% |
| `mel`   |    29.41% | 58.30% |
| `nv`    |    90.14% | 57.27% |
| `vasc`  |     0.00% |  0.00% |

### ResNet18

| Class   | Precision | Recall |
| ------- | --------: | -----: |
| `akiec` |    62.35% | 81.54% |
| `bcc`   |    77.39% | 86.41% |
| `bkl`   |    68.68% | 82.73% |
| `df`    |    78.26% | 78.26% |
| `mel`   |    57.14% | 66.37% |
| `nv`    |    95.35% | 87.25% |
| `vasc`  |    82.76% | 85.71% |

### EfficientNet-B0

| Class   | Precision | Recall |
| ------- | --------: | -----: |
| `akiec` |    64.63% | 81.54% |
| `bcc`   |    78.30% | 80.58% |
| `bkl`   |    71.05% | 73.64% |
| `df`    |    61.11% | 95.65% |
| `mel`   |    57.89% | 78.92% |
| `nv`    |    96.53% | 87.25% |
| `vasc`  |    77.14% | 96.43% |

### Evaluation Summary

| Metric                 | Best Model      | Result |
| ---------------------- | --------------- | -----: |
| Accuracy               | EfficientNet-B0 | 84.52% |
| F1 Score               | EfficientNet-B0 | 85.22% |
| Highest `nv` Precision | EfficientNet-B0 | 96.53% |
| Highest `df` Recall    | EfficientNet-B0 | 95.65% |
| Highest `vasc` Recall  | EfficientNet-B0 | 96.43% |

## Inference

The `predict.py` script can be used to classify an individual image using a trained model.

The input image can be any size. The inference pipeline automatically:

1. Loads the image.
2. Converts it to RGB.
3. Resizes it to 224 × 224.
4. Applies ImageNet normalization.
5. Loads the specified trained model.
6. Produces a predicted diagnosis.
7. Outputs the confidence of the prediction.
8. Outputs the probability for each of the seven classes.

### Usage

From the project directory:

```bash
python predict.py --model models/cnn_best.pth --image path/to/image.jpg
```

For ResNet18:

```bash
python predict.py --model models/resnet_best.pth --image path/to/image.jpg
```

For EfficientNet-B0:

```bash
python predict.py --model models/efficientnet_best.pth --image path/to/image.jpg
```

The model architecture is determined from the model filename. The filename must contain one of:

* `cnn`
* `resnet`
* `efficientnet`

### Example Output

```text
Using device: mps
Loading model: models/efficientnet_best.pth
Loading image: example.jpg

Prediction:
  Class: mel
  Confidence: 0.7892

Class Probabilities:
  akiec: 0.0214
  bcc: 0.0312
  bkl: 0.0541
  df: 0.0083
  mel: 0.7892
  nv: 0.0875
  vasc: 0.0083
```

The confidence is the softmax probability assigned to the predicted class. It represents how strongly the model favors that class relative to the other classes. It should not be interpreted as the model's actual accuracy on an individual image.

## Project Structure

```text
project/
├── training.py
├── predict.py
├── models.py
├── data/
│   ├── HAM10000_metadata.csv
│   ├── HAM10000_images_part_1/
│   └── HAM10000_images_part_2/
└── models/
    ├── cnn_best.pth
    ├── cnn_best.json
    ├── resnet_best.pth
    ├── resnet_best.json
    ├── efficientnet_best.pth
    └── efficientnet_best.json
```

## Training

To train all three models:

```bash
python training.py
```

The training script will:

1. Load the HAM10000 metadata.
2. Locate the corresponding images.
3. Create a stratified 80/20 training-validation split.
4. Calculate class weights.
5. Train the custom CNN.
6. Train ResNet18.
7. Train EfficientNet-B0.
8. Save the best model for each architecture.
9. Evaluate each model on the validation set.
10. Save the evaluation metrics as JSON files.

The best-performing model based on validation accuracy is saved automatically.

## Notes

The dataset is significantly imbalanced, so accuracy alone does not fully describe model performance. Precision, recall, and F1 score are also included to provide a better view of performance across the seven classes.
