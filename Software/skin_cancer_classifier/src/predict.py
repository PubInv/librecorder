from __future__ import annotations

import argparse
import json

from pathlib import Path

import numpy as np
import tensorflow as tf

from .config import (
    CLASS_DESCRIPTIONS,
    CLASS_NAMES,
    IMAGE_SIZE,
    MODEL_PATH,
)


def load_one_image(
    image_path: Path,
) -> tf.Tensor:
    """
    Read and resize one JPG or PNG.
    """

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: "
            f"{image_path}"
        )

    image_bytes = tf.io.read_file(
        str(image_path)
    )

    image = tf.io.decode_image(
        image_bytes,
        channels=3,
        expand_animations=False,
    )

    image = tf.image.resize_with_pad(
        image,
        target_height=IMAGE_SIZE,
        target_width=IMAGE_SIZE,
    )

    image = tf.cast(
        image,
        tf.float32,
    )

    return tf.expand_dims(
        image,
        axis=0,
    )


def predict_image(
    image_path: Path,
) -> dict[str, object]:
    """
    Predict one image.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found: "
            f"{MODEL_PATH}"
        )

    model = tf.keras.models.load_model(
        MODEL_PATH
    )

    image_batch = load_one_image(
        image_path
    )

    probabilities = model.predict(
        image_batch,
        verbose=0,
    )[0]

    predicted_index = int(
        np.argmax(probabilities)
    )

    predicted_class = (
        CLASS_NAMES[
            predicted_index
        ]
    )

    return {
        "predicted_class": predicted_class,

        "description": (
            CLASS_DESCRIPTIONS[
                predicted_class
            ]
        ),

        "confidence": float(
            probabilities[
                predicted_index
            ]
        ),

        "probabilities": {
            class_name: float(
                probabilities[
                    class_index
                ]
            )

            for class_index, class_name
            in enumerate(CLASS_NAMES)
        },
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Predict one skin-lesion image."
        )
    )

    parser.add_argument(
        "--image",
        required=True,
        type=Path,
        help="Path to a JPG or PNG image.",
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    prediction = predict_image(
        arguments.image
    )

    print(
        json.dumps(
            prediction,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()