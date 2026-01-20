import cv2
import matplotlib.pyplot as plt
from PIL import Image
import os
import numpy as np




#########################DATA AUGMENTATION##############################################################
def augment_image(image_path, num_augmentations=4):
    """Apply augmentations to a single image"""
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    image_array = Image.fromarray(image, 'RGB')
    resize_img = image_array.resize((50, 50))

    augmented = []

    # Original
    augmented.append(np.array(resize_img).astype('float32') / 255.0)

    augmentation_options = [
        lambda img: np.array(img.rotate(45)),
        lambda img: np.array(img.transpose(Image.FLIP_LEFT_RIGHT)),
        lambda img: np.array(img.rotate(90)),
        lambda img: np.array(img.transpose(Image.FLIP_TOP_BOTTOM)),
        lambda img: np.array(img.rotate(135)),
        lambda img: np.array(img.rotate(180)),
        lambda img: np.array(img.rotate(225)),
        lambda img: np.array(img.rotate(270)),
        lambda img: np.array(img.rotate(315)),
        lambda img: np.array(img.rotate(45).transpose(Image.FLIP_LEFT_RIGHT)),
        lambda img: np.array(img.rotate(45).transpose(Image.FLIP_TOP_BOTTOM)),
        lambda img: np.array(img.rotate(90).transpose(Image.FLIP_LEFT_RIGHT)),
        lambda img: np.array(img.rotate(90).transpose(Image.FLIP_TOP_BOTTOM)),
        lambda img: np.array(img.rotate(135).transpose(Image.FLIP_LEFT_RIGHT)),
        lambda img: np.array(img.rotate(135).transpose(Image.FLIP_TOP_BOTTOM)),
        lambda img: np.array(img.rotate(225).transpose(Image.FLIP_LEFT_RIGHT)),
        lambda img: np.array(img.rotate(225).transpose(Image.FLIP_TOP_BOTTOM)),
    ]

    # Apply first (num_augmentations - 1) augmentations
    for aug_func in augmentation_options[:num_augmentations - 1]:
        aug_img = aug_func(resize_img)
        augmented.append(aug_img.astype('float32') / 255.0)

    return augmented

infected = os.listdir('Data/Infected/')
uninfected = os.listdir('Data/Uninfected/')
data = []
labels = []
# Process infected (4 augmentations per image)
for i in infected:
    try:
        augmented_imgs = augment_image("Data/Infected/" + i, num_augmentations=4)
        data.extend(augmented_imgs)
        labels.extend([1] * len(augmented_imgs))
    except Exception as e:
        print(f'Error with {i}: {e}')

# Process uninfected (17 augmentations per image to balance)
for u in uninfected:
    try:
        augmented_imgs = augment_image("Data/Uninfected/" + u, num_augmentations=17)
        data.extend(augmented_imgs)
        labels.extend([0] * len(augmented_imgs))
    except Exception as e:
        print(f'Error with {u}: {e}')

cells = np.array(data)
labels = np.array(labels)

# Verify balance
print(f"Infected: {(labels == 1).sum()}")
print(f"Uninfected: {(labels == 0).sum()}")
print(f"Total: {len(labels)}")
print(f"Balance: {(labels == 0).sum() / len(labels) * 100:.1f}% uninfected")
np.save('Cells' , cells)
np.save('Labels' , labels)

#Vizualize examples of infected and not infected augmented images
plt.figure(1, figsize=(15, 9))
n = 0
for i in range(49):
    n += 1
    r = np.random.randint(0, cells.shape[0], 1)
    plt.subplot(7, 7, n)
    plt.subplots_adjust(hspace=0.5, wspace=0.5)
    plt.imshow(cells[r[0]])
    plt.title('{} : {}'.format('Infected' if labels[r[0]] == 1 else 'Uninfected',
                               labels[r[0]]))
    plt.xticks([]), plt.yticks([])

plt.show()