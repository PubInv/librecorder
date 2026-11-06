# Author Rudmila Nizam, Bangladesh University of Engineering and Technology

# Open Source Documentation for Classifier Development

## Skin Lesion Classification Using CNN

The main objective of my work is to develop a **deep learning-based image classifier** that can analyze a skin lesion image and classify it into one of seven categories.

The seven categories are:

1. Melanocytic Nevus
2. Melanoma
3. Benign Keratosis
4. Basal Cell Carcinoma
5. Actinic Keratosis
6. Vascular Lesion
7. Dermatofibroma

The dataset I selected is the **HAM10000 dataset**, which contains approximately **10,000 dermoscopic skin lesion images** belonging to these seven diagnostic categories.

---

### 1. Dataset Preparation

I first downloaded the HAM10000 dataset and organized it into two main components:

* The image files
* The metadata CSV file

The metadata contains information such as the image ID, diagnosis, age, sex, and localization.

I then connected each image to its corresponding diagnosis using the image ID.

For example, if the metadata says that a particular image has the diagnosis `mel`, I map that to **Melanoma**.

Similarly:

* `nv` → Melanocytic Nevus
* `mel` → Melanoma
* `bkl` → Benign Keratosis
* `bcc` → Basal Cell Carcinoma
* `akiec` → Actinic Keratosis
* `vasc` → Vascular Lesion
* `df` → Dermatofibroma

So essentially, I converted the raw dataset into a format that the neural network could understand.

---

### 2. Image Preprocessing

The original images do not all have exactly the same dimensions.

A neural network requires a consistent input size, so I resized every image to:

**100 × 75 pixels with 3 color channels.**

The three channels correspond to:

* Red
* Green
* Blue

So every image entering the CNN has the shape:

**75 × 100 × 3**

I also normalized the pixel values.

The reason for normalization is that neural networks generally train more effectively when the input values are on a similar scale.

---

### 3. Dividing the Dataset

I divided the available images into three groups:

* **Training set — 72%**
* **Validation set — 8%**
* **Testing set — 20%**

The training set is used to actually teach the model.

The validation set is used during training to monitor whether the model is learning properly and to decide when to stop training.

The test set is kept separate and is used at the end to estimate how well the model performs on images it has not seen during training.

I also used **stratified splitting** for the initial train/test split so that the different disease classes are represented more consistently in both groups.

---

### 4. What Model Did I Choose?

The model I implemented is a **Convolutional Neural Network, or CNN**.

I did not use architectures such as:

* Swin Transformer
* ConvNeXt
* EfficientNet

My current model is a **custom/basic CNN architecture** built using convolutional layers, pooling layers, dropout layers, and fully connected layers.

The basic structure is:

**Image → Convolution → Convolution → Pooling → Dropout → Convolution → Convolution → Pooling → Dropout → Fully Connected Layer → Output**

---

### 5. What Does the CNN Actually Do?

The most important concept is understanding what the CNN is actually learning.

When I give the network a skin lesion image, it does not directly understand that the image is "melanoma" or "nevus."

Instead, it gradually learns visual patterns.

In the first convolutional layers, it can learn relatively simple features such as:

* Edges
* Lines
* Color transitions
* Simple textures

In deeper layers, these features are combined to recognize more complicated patterns such as:

* Shapes
* Lesion boundaries
* Texture patterns
* Color distributions
* Structural characteristics of the lesion

Finally, the network combines all of these learned features and produces seven probabilities corresponding to the seven disease categories.

For example, a prediction could look conceptually like:

Melanoma → 75%

Melanocytic Nevus → 15%

Benign Keratosis → 5%

and so on.

The class with the highest probability becomes the model's predicted class.

---

### 6. Convolutional Layers

My CNN starts with convolutional layers.

The first convolutional layer has **32 filters**.

A filter is basically a small mathematical window that moves across the image and looks for particular patterns.

The first layer might learn simple visual structures.

Then I have another convolutional layer with 32 filters.

After that, I use a **Max Pooling layer**.

Pooling reduces the spatial size of the feature maps.

This makes the computation smaller and helps the network focus on the most important features.

---

### 7. Deeper Feature Extraction

The next block contains convolutional layers with **64 filters**.

The number of filters increases from 32 to 64 because deeper layers need to learn more complex patterns.

So the general idea is:

**Early layers → simple features**

**Middle layers → more complex features**

**Later layers → disease-related visual patterns**

---

### 8. Dropout

I also included dropout layers.

Dropout is a technique used to reduce **overfitting**.

Overfitting means that the model becomes very good at remembering the training images but performs poorly on new images.

During training, dropout temporarily removes some neurons from the network.

This forces the model to learn more robust patterns instead of depending too heavily on particular neurons.

I used dropout rates of:

* 0.25
* 0.40
* 0.50

at different parts of the network.

---

### 9. Fully Connected Layer

After the convolutional layers, I use a **Flatten layer**.

The feature maps produced by the convolutional layers are converted into a one-dimensional representation.

Then I use a dense layer containing **128 neurons**.

This layer combines the visual features extracted by the CNN and uses them to make the final classification.

Finally, I use a dense layer containing **7 neurons** because there are seven possible disease categories.

---

### 10. Softmax Output

The final layer uses the **softmax activation function**.

Softmax converts the network's outputs into probabilities.

For example:

| Disease              | Probability |
| -------------------- | ----------: |
| Melanoma             |         75% |
| Melanocytic Nevus    |         12% |
| Benign Keratosis     |          5% |
| Basal Cell Carcinoma |          4% |
| Others               |          4% |

The model would therefore select Melanoma as the predicted class.

---

### 11. Data Augmentation

I also implemented **data augmentation**.

This means creating slightly modified versions of existing training images.

For example, I allow:

* Rotation
* Zooming
* Horizontal flipping
* Width shifting
* Height shifting

The purpose is to expose the model to slightly different versions of the same type of lesion.

This can help reduce overfitting and improve the model's ability to generalize to unseen images.

---

### 12. Training

I trained the CNN using the **Adam optimizer**.

The initial learning rate was:

**0.001**

The model uses **categorical cross-entropy** as the loss function because this is a multi-class classification problem.

I initially allowed training for up to **50 epochs**.

However, I also implemented:

**Early Stopping**

and

**ReduceLROnPlateau**

Early stopping prevents unnecessary training when the validation performance stops improving.

ReduceLROnPlateau reduces the learning rate when the validation performance stops improving, allowing the model to make smaller adjustments during later stages of training.

---

### 13. Current Result

With the current CNN architecture, I obtained approximately **75% test accuracy**.

This shows that the model has learned meaningful visual patterns from the HAM10000 dataset.

However, I don't consider 75% accuracy to be the final result.

There are important limitations in the dataset, particularly **class imbalance**.

Some disease categories have many more images than others.

Therefore, a model can obtain a reasonable overall accuracy while still performing poorly on minority classes.

For a medical classification problem, this is particularly important.

---

### 14. What I Want to Improve Next

My next step is therefore not simply to increase the accuracy number.

I want to evaluate the model more carefully using:

* Precision
* Recall
* F1-score
* Confusion matrix
* Per-class performance

This will allow me to determine which disease categories the model handles well and which categories it struggles with.

For example, if the model performs very well on Melanocytic Nevus but poorly on Melanoma or Actinic Keratosis, overall accuracy alone would hide that problem.

---

### 15. Future Model Comparison

After establishing this baseline CNN, I would like to compare it with stronger modern architectures.

Possible models include:

**EfficientNet**

**ConvNeXt**

**Swin Transformer**

These architectures have different approaches to extracting visual information.

The idea is not simply to replace my current model immediately.

Instead, I want to establish the current CNN as a **baseline**, evaluate it properly, and then compare the newer architectures under similar preprocessing and evaluation conditions.

This will allow us to determine whether a more advanced architecture actually provides a meaningful improvement.

---

### 16. Testing an External Image

I have also implemented an inference stage where I can upload an external image and pass it through the trained model.

The image is first:

1. Loaded
2. Converted to RGB
3. Resized to 100 × 75 pixels
4. Normalized
5. Passed through the trained CNN

The model then produces seven probabilities.

The highest probability is selected as the predicted class.

This gives us a basic demonstration of how the trained classifier can be used on a new image.

However, I want to emphasize that this should be treated as a **research screening demonstration**, not as a medical diagnostic tool.

A prediction from this model cannot replace evaluation by a dermatologist.

---

### 17. Current Status

So, at this point, I have completed:

**Dataset preparation → Image preprocessing → Train/validation/test splitting → CNN implementation → Data augmentation → Model training → Testing → Model saving → External-image inference**

The current baseline CNN achieves approximately **75% test accuracy**.

My next priority is to perform a more comprehensive evaluation, particularly because of the class imbalance, and then compare this baseline against architectures such as EfficientNet, ConvNeXt, and Swin Transformer.

## Deep Learning Work Onward checked Efficient net ,MobilenetV2

My work can be divided into three main stages:

first, dataset preparation and leakage-controlled splitting;

second, development and evaluation of conventional deep learning baselines;

and third, implementation and evaluation of DermLIP-PanDerm.

---

### 1. Dataset Preparation

I used the **HAM10000 dataset**, consisting of 10,015 dermoscopic images from seven diagnostic categories.

The seven classes are **Actinic Keratosis, Basal Cell Carcinoma, Benign Keratosis, Dermatofibroma, Melanoma, Melanocytic Nevus, and Vascular Lesion**.

The dataset is highly imbalanced. Melanocytic nevus represents the majority of the dataset, while dermatofibroma and vascular lesion have considerably fewer samples.

Because of this imbalance, I did not consider accuracy as the only evaluation metric.

I evaluated the models using **accuracy, balanced accuracy, macro precision, macro recall, macro F1-score, and weighted F1-score**, together with the confusion matrix.

---

### 2. Lesion-Level Data Splitting

A major concern during dataset preparation was **data leakage**.

HAM10000 contains multiple images associated with the same lesion. Therefore, randomly dividing individual images could result in images from the same lesion appearing in both training and testing sets.

To avoid this, I performed the splitting based on **lesion ID**.

The dataset was divided into approximately **70% training, 10% validation, and 20% testing**.

The resulting split contains:

* **7,048 training images**
* **977 validation images**
* **1,990 testing images**

The test set was kept completely separate from model training.

Therefore, when I report test performance, it represents performance on **held-out HAM10000 images that were not used to train the model**.

---

### 3. Baseline Models

After completing the preprocessing and splitting, I established three conventional deep learning baselines.

The models were:

**Custom CNN, MobileNetV2, and EfficientNetB0.**

The purpose of these experiments was to establish a reference performance before applying the dermatology-specific foundation model.

The Custom CNN achieved **51.76% accuracy**, with a balanced accuracy of **44.87%** and a macro F1-score of **31.88%**.

MobileNetV2 achieved **38.89% accuracy**, with a balanced accuracy of **26.91%** and a macro F1-score of **21.26%**.

Among these three models, **EfficientNetB0 performed the best**.

It achieved:

**67.34% accuracy,

61.67% balanced accuracy,

46.91% macro precision,

61.67% macro recall,

50.48% macro F1-score,

and 70.36% weighted F1-score.**

Therefore, EfficientNetB0 became my primary conventional baseline.

---

### 4. Transition to DermLIP-PanDerm

After establishing the baseline, I moved to the next stage, which was the implementation of **DermLIP-PanDerm**.

The reason for using DermLIP-PanDerm is that it is designed specifically for dermatological image representation.

The conventional CNN models in my baseline learn their task-specific representations from the HAM10000 training set.

In contrast, DermLIP-PanDerm provides a pretrained representation learned from large-scale dermatological image and text data.

Therefore, my research question at this stage is:

**Can a dermatology-specific pretrained representation provide more useful features for HAM10000 classification than conventional deep learning models?**

---

### 5. DermLIP-PanDerm Approach

In the current experiment, I use the **image encoder of DermLIP-PanDerm**.

The HAM10000 dermoscopic image is first processed using the preprocessing required by the pretrained model.

The image is then passed through the pretrained visual encoder.

This produces a **512-dimensional image embedding**.

The downstream architecture is therefore:

**HAM10000 image → DermLIP-PanDerm image encoder → 512-dimensional embedding → seven-class linear classifier.**

For the first experiment, I keep the pretrained image encoder **frozen**.

I train only the linear classification layer.

This experiment is referred to as **linear probing**.

The purpose is to determine how discriminative the pretrained dermatological features are without modifying the pretrained encoder.

---

### 6. Implementation Challenge

During implementation, I encountered a technical issue with the pretrained model.

Initially, I attempted to load the DermLIP-PanDerm checkpoint using the standard OpenCLIP implementation.

The checkpoint was downloaded successfully, but the model failed during state-dictionary loading.

The error showed a mismatch between the expected parameters and the parameters contained in the pretrained checkpoint.

The standard OpenCLIP implementation expected conventional CLIP Vision Transformer parameters, while the DermLIP-PanDerm checkpoint contained **PanDerm-specific Vision Transformer components**.

Therefore, the problem was an **architecture mismatch**, rather than a problem with the pretrained checkpoint itself.

I resolved this by using the compatible implementation from the **PanDerm/Derm1M codebase** instead of relying on the incompatible generic implementation.

After making this change, the model loaded successfully.

I verified the model structure and confirmed the availability of both the image and text encoders.

Therefore, the DermLIP-PanDerm implementation is now functioning correctly and can be used for the HAM10000 downstream experiment.

---

### 7. DermLIP-PanDerm Linear Probe Results

I have now completed the first DermLIP-PanDerm experiment using a linear probe.

The results are as follows.

For the **training set**, the model achieved:

**69.07% accuracy**,

**18.27% balanced accuracy**,

and **18.41% macro F1-score**.

For the **validation set**, it achieved:

**69.28% accuracy**,

**18.43% balanced accuracy**,

and **18.89% macro F1-score**.

Finally, on the held-out **test set**, the model achieved:

**69.28% accuracy**,

**18.07% balanced accuracy**,

and **18.18% macro F1-score**.

The weighted F1-score on the test set was **59.93%**.

---

### 8. Interpretation of the Results

The most important point in these results is that **69.28% accuracy should not be interpreted by itself**.

Although the DermLIP-PanDerm linear probe achieved a higher raw accuracy than my EfficientNetB0 baseline, which achieved 67.34%, its balanced accuracy and macro F1-score are substantially lower.

EfficientNetB0 achieved **61.67% balanced accuracy and 50.48% macro F1**, whereas the DermLIP-PanDerm linear probe achieved only **18.07% balanced accuracy and 18.18% macro F1** on the test set.

This indicates that the linear probe is likely relying heavily on the **majority class** and is not adequately separating the minority diagnostic categories.

Therefore, based on the current results, I cannot claim that DermLIP-PanDerm is superior to EfficientNetB0.

In fact, based on balanced performance across the seven classes, **EfficientNetB0 is currently the stronger model**.

The linear-probe result is useful because it tells me that the frozen DermLIP-PanDerm representation, when combined with a simple linear classifier, is not sufficient for this particular seven-class HAM10000 classification task.

---

### 9. Next Step: Fine-Tuning

Based on this result, the next stage of my work is **supervised fine-tuning of DermLIP-PanDerm**.

The current linear-probe experiment keeps the image encoder frozen.

In the next experiment, I will allow the pretrained representation to adapt to the HAM10000 classification task.

The classification head will produce seven outputs corresponding to the seven diagnostic classes.

I will then compare:

**EfficientNetB0,**

**DermLIP-PanDerm with linear probing,**

and

**DermLIP-PanDerm with supervised fine-tuning.**

The objective is to determine whether fine-tuning allows the pretrained dermatological representation to better separate the seven HAM10000 classes.

---

### 10. Final Evaluation Strategy

For the final comparison, I will maintain the same lesion-level test set across the experiments.

I will compare the models using:

**Accuracy, balanced accuracy, macro precision, macro recall, macro F1, and weighted F1.**

I will also examine the confusion matrix and class-wise recall.

This is particularly important because a model can obtain relatively high accuracy by correctly predicting the majority class while performing poorly on the minority classes.

Therefore, for this project, I consider **macro-level and balanced metrics more informative than raw accuracy alone**.

---

### 11. Current Status

At this point, the major preprocessing and baseline stages have been completed.

The HAM10000 dataset has been processed using lesion-level splitting.

The conventional models have been trained and evaluated.

EfficientNetB0 is currently my best baseline with **67.34% test accuracy and 50.48% macro F1-score**.

The DermLIP-PanDerm model has also been successfully implemented after resolving the architecture compatibility issue.

The initial linear-probe experiment has been completed.

It produced **69.28% test accuracy**, but only **18.07% balanced accuracy and 18.18% macro F1-score**.

Therefore, the current result indicates that the frozen pretrained representation requires further adaptation for this classification task.

---

### 12. Conclusion

To conclude, my work has progressed from conventional CNN-based classification toward the use of a dermatology-specific foundation model.

The dataset preparation and leakage-controlled splitting have been completed.

Three conventional deep learning models were evaluated, with EfficientNetB0 providing the strongest baseline.

I then implemented DermLIP-PanDerm and resolved the pretrained-model architecture mismatch.

The first linear-probe experiment has been completed.

Although its raw accuracy is **69.28%**, its low balanced accuracy and macro F1 indicate poor performance across the seven classes.

Therefore, I am now proceeding to the **fine-tuning stage**, which will determine whether adapting the pretrained DermLIP-PanDerm representation can improve class-balanced performance on HAM10000.

## Panderm on DDI Dataset

*PanDerm-Large Evaluation on the DDI Dataset*

### 1. Introduction and objective

I evaluated the pretrained PanDerm-Large model on the Diverse Dermatology Images (DDI) dataset using the PanDerm_Large_LP model configuration, where LP refers to the linear-probe evaluation setup.

My main objective was to assess how well the pretrained model generalizes to an external dermatology dataset, particularly for distinguishing benign from malignant skin lesions.

I was also interested in identifying potential weaknesses in malignant lesion detection, because missing a malignant case can be more serious than generating a false alarm.

The DDI dataset contains clinical photographs of skin lesions from patients with diverse skin tones. The dataset includes biopsy-confirmed diagnoses and is useful for examining model performance across different skin-tone groups.

### 2. Dataset preparation

The original DDI dataset contained 656 images. After preprocessing, 647 images were included in the evaluation workflow.

The dataset was divided into training, validation, and test sets:

- Training: 427 images
- Validation: 83 images
- Test: 137 images

The classification task was binary:

- Benign: negative class
- Malignant: positive class

I used the pretrained PanDerm-Large checkpoint and evaluated it with the PanDerm_Large_LP configuration. The model was evaluated using the official linear-probe pipeline.

### 3. Baseline performance

The model achieved the following results on the DDI test set:

| Metric | Result |
| --- | ---: |
| Accuracy | 80.29% |
| Balanced accuracy | 78.67% |
| Macro precision | 72.51% |
| Macro recall | 78.67% |
| Macro F1-score | 74.34% |
| Weighted precision | 84.11% |
| Weighted recall | 80.29% |
| Weighted F1-score | 81.47% |

Overall, PanDerm-Large demonstrated promising classification performance on the external DDI test set.

However, accuracy alone does not fully describe the model's ability to identify malignant lesions. I therefore examined the confusion matrix and class-specific recall.

### 4. Malignant lesion detection

The model correctly classified 22 of the 29 malignant cases, while 7 malignant cases were incorrectly classified as benign.

The resulting malignant-lesion metrics were:

- Sensitivity (recall): 75.86%
- Specificity: 81.48%
- Precision: 52.38%
- False negatives: 7
- False positives: 20

This shows that the model detected approximately three-quarters of the malignant cases in the test set. However, some malignant lesions were still missed, and a substantial number of benign lesions were classified as malignant.

### 5. Comparison with the earlier zero-shot evaluation

Before running the official PanDerm linear-probe evaluation, I also tested a DermLIP model using a zero-shot image–text similarity approach.

The zero-shot model had a malignant recall of 84.80%, but its benign recall was only 36.49%. It therefore tended to classify many benign lesions as malignant.

The official PanDerm-Large linear-probe evaluation produced a more balanced result, with 80.29% accuracy and 78.67% balanced accuracy.

These are two different evaluation approaches, so this comparison should not be interpreted as a controlled comparison of the same model under identical conditions.

### 6. Skin-tone subgroup analysis

I also examined the zero-shot results across Fitzpatrick skin-tone groups to investigate whether performance differed across groups.

In this preliminary zero-shot analysis, malignant recall was relatively high across the three groups, but benign recall was considerably lower. Accuracy and balanced accuracy also varied by skin-tone group.

| Experiment | Model | Reported test accuracy |
| --- | --- | --- |
| Earlier CNN | basic CNN | ~75% |
| Later comparative evaluation | Custom CNN | 51.76% |
| Later comparative evaluation | MobileNetV2 | 38.89% |
| Later comparative evaluation | EfficientNetB0 | 67.34% |

These findings motivate further subgroup analysis using the official linear-probe model. The table above represents the zero-shot evaluation, not the official PanDerm-Large linear-probe results.

### 7. Next step: reduce malignant false negatives

The next step is to investigate whether malignant sensitivity can be improved while limiting the increase in false positives.

For DDI, the appropriate next experiment would be:

1. Extracting the model's malignant-class probability scores.
1. Evaluating different decision thresholds using the validation set.
1. Comparing sensitivity, specificity, false negatives, and false positives at each threshold.
1. Selecting an operating point that meets a predefined specificity target while improving malignant sensitivity.
1. Evaluating the selected threshold once on the held-out test set.

### 8. Conclusion

I evaluated the pretrained PanDerm-Large model using the PanDerm_Large_LP configuration on the DDI external test set. The model achieved 80.29% accuracy, 78.67% balanced accuracy, and 81.47% weighted F1-score.

For malignant lesion detection, sensitivity was 75.86%, with 7 false-negative cases and 20 false-positive cases. These results provide a baseline for investigating the trade-off between malignant sensitivity and specificity.

The next step is to perform validation-based threshold optimization and assess whether malignant false negatives can be reduced without an unacceptable increase in false positives.

## Panderm on Ham-10000 Dataset

More specifically, I used the PanDerm_Large_LP model configuration, where LP refers to the linear-probe evaluation setup.

My main focus was not only to evaluate the overall classification performance, but also to improve melanoma detection, because missing melanoma cases can be more serious than producing some false alarms.

The HAM10000 dataset contains seven skin lesion classes:

- AKIEC
- BCC
- BKL
- DF
- Melanoma
- Nevus
- Vascular lesion

I prepared the dataset using a lesion-aware train, validation, and test split. This means that images belonging to the same lesion were kept within the same split, which helps prevent data leakage.

Then I loaded the pretrained PanDerm-Large checkpoint and evaluated it using the PanDerm_Large_LP configuration.

For every image, the model generated:

- a predicted class
- and probability scores for all seven lesion classes

### Baseline Performance

First, I evaluated the original PanDerm predictions.

The baseline results were:

- Accuracy: 84.63%
- Weighted F1-score: 84.26%
- Balanced accuracy: 68.24%
- Overall AUROC: 95.13%
- Overall AUPR: 78.70%

So, overall, the pretrained PanDerm-Large model showed strong classification performance.

However, after analyzing the confusion matrix, I found an important problem with melanoma detection.

There were 223 actual melanoma cases in the test set.

Out of those:

- 130 were correctly detected as melanoma
- 93 were missed

Therefore, the melanoma sensitivity, or recall, was only:

58.3%

The biggest confusion was between melanoma and nevus.

The model classified 69 actual melanoma cases as nevus.

This is important because these are melanoma false negatives, meaning real melanoma cases were missed.

The baseline melanoma specificity was approximately 96.1%.

So the model was very good at avoiding false melanoma alarms, but its melanoma sensitivity was relatively low.

### Melanoma ROC Analysis

I also analyzed the melanoma-specific ROC curve.

For this analysis, I treated:

- melanoma as the positive class
- all other six lesion classes as the negative class

In the PanDerm prediction output, melanoma corresponds to class 4, so I used:

probability_class_4

as the melanoma confidence score.

The melanoma-specific ROC-AUC was:

0.919

This means the model has strong ability to distinguish melanoma from non-melanoma images based on its probability scores.

However, although the ROC-AUC was good, the original decision rule still missed many melanoma cases.

So I focused on improving the decision threshold.

### Improvement Method

I did not retrain PanDerm-Large, and I did not change the architecture or pretrained weights.

Instead, I applied a melanoma-specific threshold optimization as a post-processing step.

Normally, the classifier selects the class with the highest probability.

For example, if:

- Nevus probability = 0.45
- Melanoma probability = 0.40

the original model predicts Nevus, because 0.45 is the highest probability.

But because melanoma detection is more critical, I tested different melanoma probability thresholds.

If the melanoma probability was above the selected threshold, I classified that image as melanoma, even when another class had a slightly higher probability.

So my modification was in the final decision rule, not in the PanDerm model itself.

### Results After Optimization

After applying the optimized melanoma threshold, the melanoma result improved.

Before optimization:

- True positives = 130
- False negatives = 93
- Sensitivity = 58.3%

After optimization:

- True positives = 160
- False negatives = 63
- Sensitivity = 71.75%

So I detected 30 additional melanoma cases.

The number of missed melanoma cases decreased from:

93 to 63

and melanoma sensitivity increased from:

58.3% to 71.75%

This is an improvement of about 13.45 percentage points in melanoma sensitivity.

### Trade-Off

However, there was a trade-off.

Because I lowered the melanoma threshold, some non-melanoma cases were also classified as melanoma.

Therefore, false positives increased.

The melanoma specificity changed from approximately:

96.1% before optimization

to:

91.8% after optimization

The overall accuracy also decreased slightly:

- Before: 84.63%
- After: 82.83%

And weighted F1 changed from:

- 84.26%
- to 83.10%

So my goal was not to maximize overall accuracy.

My goal was to reduce melanoma false negatives and improve melanoma sensitivity.

In a screening application, this trade-off can be useful because identifying more possible melanoma cases may be more important than avoiding every false alarm.

### Conclusion

In conclusion, I evaluated the pretrained PanDerm-Large model using the PanDerm_Large_LP configuration on the HAM10000 dataset.

The baseline model achieved:

- 84.63% accuracy
- 84.26% weighted F1
- 95.13% overall AUROC

The melanoma-specific ROC-AUC was:

0.919

However, the original melanoma sensitivity was only 58.3%, with 93 false-negative melanoma cases.

Therefore, I applied melanoma-specific threshold optimization.

After optimization:

- melanoma sensitivity increased to 71.75%
- true positives increased from 130 to 160
- false negatives decreased from 93 to 63

So my main contribution in this experiment was improving the melanoma operating point by changing the decision threshold, while keeping the original pretrained PanDerm-Large model unchanged.
