from __future__ import annotations

from pathlib import Path

import pandas as pd
import tensorflow as tf

from .config import (
    BATCH_SIZE,
    IMAGE_SIZE,
    PROJECT_ROOT,
    RANDOM_SEED,
)


def read_split_csv(
    csv_path: Path,
) -> pd.DataFrame:
    """
    Read one generated data split.
    """

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Missing split file: "
            f"{csv_path}\n"
            "Run this command first:\n"
            "python -m src.prepare_data"
        )

    dataframe = pd.read_csv(
        csv_path
    )

    required_columns = {
        "image_path",
        "label",
        "dx",
    }

    missing_columns = (
        required_columns
        - set(dataframe.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Split CSV is missing columns: "
            f"{sorted(missing_columns)}"
        )

    return dataframe


def make_absolute_paths(
    dataframe: pd.DataFrame,
) -> list[str]:
    """
    Convert stored project-relative paths
    into complete image paths.
    """

    return [
        str(
            (
                PROJECT_ROOT
                / relative_path
            ).resolve()
        )
        for relative_path
        in dataframe[
            "image_path"
        ].astype(str)
    ]


def decode_and_resize(
    image_path: tf.Tensor,
    label: tf.Tensor,
) -> tuple[tf.Tensor, tf.Tensor]:
    """
    Read and resize one image.
    """

    image_bytes = tf.io.read_file(
        image_path
    )

    image = tf.io.decode_jpeg(
        image_bytes,
        channels=3,
    )

    image = tf.image.resize_with_pad(
        image,
        target_height=IMAGE_SIZE,
        target_width=IMAGE_SIZE,
        method="bilinear",
    )

    image = tf.cast(
        image,
        tf.float32,
    )

    label = tf.cast(
        label,
        tf.int32,
    )

    return image, label


def build_dataset(
    dataframe: pd.DataFrame,
    training: bool,
    batch_size: int = BATCH_SIZE,
) -> tf.data.Dataset:
    """
    Create a TensorFlow dataset.
    """

    image_paths = make_absolute_paths(
        dataframe
    )

    labels = (
        dataframe["label"]
        .astype("int32")
        .to_numpy()
    )

    dataset = (
        tf.data.Dataset
        .from_tensor_slices(
            (image_paths, labels)
        )
    )

    if training:
        dataset = dataset.shuffle(
            buffer_size=len(dataframe),
            seed=RANDOM_SEED,
            reshuffle_each_iteration=True,
        )

    dataset = dataset.map(
        decode_and_resize,
        num_parallel_calls=(
            tf.data.AUTOTUNE
        ),
    )

    dataset = dataset.batch(
        batch_size
    )

    dataset = dataset.prefetch(
        tf.data.AUTOTUNE
    )

    return dataset