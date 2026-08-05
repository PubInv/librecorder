from __future__ import annotations

import tensorflow as tf
from tensorflow.keras import (
    layers,
    models,
)

from .config import (
    CLASS_NAMES,
    IMAGE_SIZE,
)


def convolution_block(
    inputs: tf.Tensor,
    filters: int,
    dropout_rate: float,
) -> tf.Tensor:
    """
    Reusable convolution block.
    """

    x = layers.Conv2D(
        filters=filters,
        kernel_size=3,
        padding="same",
        use_bias=False,
    )(inputs)

    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    x = layers.Conv2D(
        filters=filters,
        kernel_size=3,
        padding="same",
        use_bias=False,
    )(x)

    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    x = layers.MaxPooling2D(
        pool_size=2
    )(x)

    x = layers.Dropout(
        dropout_rate
    )(x)

    return x


def build_baseline_cnn() -> tf.keras.Model:
    """
    Create a seven-class CNN.
    """

    inputs = layers.Input(
        shape=(
            IMAGE_SIZE,
            IMAGE_SIZE,
            3,
        ),
        name="image",
    )

    data_augmentation = models.Sequential(
        [
            layers.RandomFlip(
                "horizontal_and_vertical"
            ),
            layers.RandomRotation(
                0.08
            ),
            layers.RandomZoom(
                0.10
            ),
            layers.RandomTranslation(
                0.05,
                0.05,
            ),
            layers.RandomContrast(
                0.10
            ),
        ],
        name="data_augmentation",
    )

    x = data_augmentation(inputs)

    # Normalize pixel values from
    # 0–255 to 0–1.
    x = layers.Rescaling(
        scale=1.0 / 255.0,
        name="normalize_pixels",
    )(x)

    x = convolution_block(
        x,
        filters=32,
        dropout_rate=0.10,
    )

    x = convolution_block(
        x,
        filters=64,
        dropout_rate=0.15,
    )

    x = convolution_block(
        x,
        filters=128,
        dropout_rate=0.20,
    )

    x = convolution_block(
        x,
        filters=256,
        dropout_rate=0.25,
    )

    x = layers.GlobalAveragePooling2D()(
        x
    )

    x = layers.Dense(
        128,
        activation="relu",
    )(x)

    x = layers.Dropout(
        0.40
    )(x)

    outputs = layers.Dense(
        len(CLASS_NAMES),
        activation="softmax",
        name="class_probabilities",
    )(x)

    return models.Model(
        inputs=inputs,
        outputs=outputs,
        name="ham10000_baseline_cnn",
    )