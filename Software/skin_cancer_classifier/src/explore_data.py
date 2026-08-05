from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

from .config import (
    CLASS_NAMES,
    IMAGE_DIRS,
    METADATA_CSV,
    REPORT_DIR,
    ensure_output_directories,
)


def build_image_lookup() -> dict[str, Path]:
    """
    Create a mapping between image IDs
    and their JPG file paths.
    """

    image_lookup: dict[str, Path] = {}

    for image_directory in IMAGE_DIRS:
        if not image_directory.exists():
            raise FileNotFoundError(
                f"Missing image directory: "
                f"{image_directory}"
            )

        for image_path in image_directory.glob(
            "*.jpg"
        ):
            image_lookup[
                image_path.stem
            ] = image_path

    return image_lookup


def save_class_distribution(
    metadata: pd.DataFrame,
) -> None:
    """
    Create a graph showing how many
    images belong to every class.
    """

    class_counts = (
        metadata["dx"]
        .value_counts()
        .reindex(
            CLASS_NAMES,
            fill_value=0,
        )
    )

    plt.figure(figsize=(9, 5))

    class_counts.plot(kind="bar")

    plt.title(
        "HAM10000 Class Distribution"
    )

    plt.xlabel("Class")
    plt.ylabel("Number of Images")
    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(
        REPORT_DIR
        / "class_distribution.png",
        dpi=150,
    )

    plt.close()


def save_sample_images(
    metadata: pd.DataFrame,
    image_lookup: dict[str, Path],
) -> None:
    """
    Save one sample image from every class.
    """

    figure, axes = plt.subplots(
        2,
        4,
        figsize=(12, 7),
    )

    axes = axes.flatten()

    for index, class_name in enumerate(
        CLASS_NAMES
    ):
        sample_row = metadata.loc[
            metadata["dx"] == class_name
        ].iloc[0]

        image_id = sample_row["image_id"]

        image_path = image_lookup[image_id]

        with Image.open(image_path) as image:
            axes[index].imshow(
                image.convert("RGB")
            )

        axes[index].set_title(class_name)
        axes[index].axis("off")

    # Eight spaces are available,
    # but the dataset has seven classes.
    axes[-1].axis("off")

    figure.suptitle(
        "One Example from Each HAM10000 Class"
    )

    figure.tight_layout()

    figure.savefig(
        REPORT_DIR / "sample_images.png",
        dpi=150,
    )

    plt.close(figure)


def main() -> None:
    ensure_output_directories()

    if not METADATA_CSV.exists():
        raise FileNotFoundError(
            f"Metadata file not found: "
            f"{METADATA_CSV}"
        )

    metadata = pd.read_csv(
        METADATA_CSV
    )

    image_lookup = build_image_lookup()

    print("Dataset shape:")
    print(metadata.shape)

    print("\nMetadata columns:")
    print(metadata.columns.tolist())

    print("\nFirst five metadata rows:")
    print(metadata.head())

    print("\nMissing values:")
    print(metadata.isna().sum())

    print("\nImages in each class:")
    print(
        metadata["dx"]
        .value_counts()
        .reindex(
            CLASS_NAMES,
            fill_value=0,
        )
    )

    print(
        "\nNumber of unique lesions:",
        metadata["lesion_id"].nunique(),
    )

    print(
        "Number of images found:",
        len(image_lookup),
    )

    missing_image_ids = sorted(
        set(metadata["image_id"])
        - set(image_lookup)
    )

    print(
        "Images referenced in metadata "
        "but not found:",
        len(missing_image_ids),
    )

    save_class_distribution(metadata)

    save_sample_images(
        metadata,
        image_lookup,
    )

    print(
        "\nReports saved in:",
        REPORT_DIR,
    )


if __name__ == "__main__":
    main()