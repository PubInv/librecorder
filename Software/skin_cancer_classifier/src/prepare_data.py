from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import (
    StratifiedGroupKFold,
)

from .config import (
    CLASS_NAMES,
    IMAGE_DIRS,
    METADATA_CSV,
    PROJECT_ROOT,
    RANDOM_SEED,
    SPLIT_DIR,
    TEST_CSV,
    TRAIN_CSV,
    VAL_CSV,
    ensure_output_directories,
)


def build_image_lookup(
    image_directories: tuple[Path, ...],
) -> dict[str, str]:
    """
    Map image_id to a project-relative
    path such as:

    data/raw/HAM10000_images_part_1/
    ISIC_0024306.jpg
    """

    image_lookup: dict[str, str] = {}

    for image_directory in image_directories:
        if not image_directory.exists():
            raise FileNotFoundError(
                f"Missing image directory: "
                f"{image_directory}\n"
                "Extract the Kaggle dataset "
                "into data/raw first."
            )

        for image_path in image_directory.glob(
            "*.jpg"
        ):
            image_id = image_path.stem

            if image_id in image_lookup:
                raise ValueError(
                    f"Duplicate image ID: "
                    f"{image_id}"
                )

            relative_path = (
                image_path.relative_to(
                    PROJECT_ROOT
                )
            )

            image_lookup[image_id] = (
                relative_path.as_posix()
            )

    if not image_lookup:
        raise RuntimeError(
            "No JPG files were found."
        )

    return image_lookup


def validate_metadata(
    metadata: pd.DataFrame,
) -> None:
    """
    Check metadata before splitting.
    """

    required_columns = {
        "image_id",
        "lesion_id",
        "dx",
    }

    missing_columns = (
        required_columns
        - set(metadata.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Missing required metadata "
            f"columns: {sorted(missing_columns)}"
        )

    important_columns = [
        "image_id",
        "lesion_id",
        "dx",
    ]

    if metadata[
        important_columns
    ].isna().any().any():
        raise ValueError(
            "Missing values were found in "
            "image_id, lesion_id or dx."
        )

    unexpected_labels = sorted(
        set(metadata["dx"])
        - set(CLASS_NAMES)
    )

    if unexpected_labels:
        raise ValueError(
            f"Unexpected diagnosis labels: "
            f"{unexpected_labels}"
        )

    if metadata[
        "image_id"
    ].duplicated().any():
        raise ValueError(
            "Duplicate image_id values found."
        )

    diagnoses_per_lesion = (
        metadata
        .groupby("lesion_id")["dx"]
        .nunique()
    )

    inconsistent_lesions = (
        diagnoses_per_lesion[
            diagnoses_per_lesion > 1
        ]
    )

    if not inconsistent_lesions.empty:
        raise ValueError(
            "At least one lesion_id has "
            "more than one diagnosis."
        )


def take_first_grouped_fold(
    dataframe: pd.DataFrame,
    number_of_splits: int,
    random_seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Select one stratified grouped fold.

    Grouping prevents the same lesion_id
    from appearing in both returned sets.
    """

    splitter = StratifiedGroupKFold(
        n_splits=number_of_splits,
        shuffle=True,
        random_state=random_seed,
    )

    remaining_indices, holdout_indices = next(
        splitter.split(
            X=dataframe["image_path"],
            y=dataframe["dx"],
            groups=dataframe["lesion_id"],
        )
    )

    remaining_dataframe = dataframe.iloc[
        remaining_indices
    ].copy()

    holdout_dataframe = dataframe.iloc[
        holdout_indices
    ].copy()

    return (
        remaining_dataframe,
        holdout_dataframe,
    )


def verify_no_lesion_leakage(
    training_dataframe: pd.DataFrame,
    validation_dataframe: pd.DataFrame,
    test_dataframe: pd.DataFrame,
) -> None:
    """
    Confirm that a lesion occurs in only
    one dataset split.
    """

    training_lesions = set(
        training_dataframe["lesion_id"]
    )

    validation_lesions = set(
        validation_dataframe["lesion_id"]
    )

    test_lesions = set(
        test_dataframe["lesion_id"]
    )

    if training_lesions & validation_lesions:
        raise RuntimeError(
            "Lesion leakage between "
            "training and validation."
        )

    if training_lesions & test_lesions:
        raise RuntimeError(
            "Lesion leakage between "
            "training and testing."
        )

    if validation_lesions & test_lesions:
        raise RuntimeError(
            "Lesion leakage between "
            "validation and testing."
        )


def add_numeric_labels(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert diagnosis names into integers.

    akiec = 0
    bcc   = 1
    bkl   = 2
    df    = 3
    mel   = 4
    nv    = 5
    vasc  = 6
    """

    dataframe = dataframe.copy()

    dataframe["label"] = pd.Categorical(
        dataframe["dx"],
        categories=CLASS_NAMES,
        ordered=True,
    ).codes

    if (
        dataframe["label"] < 0
    ).any():
        raise ValueError(
            "A diagnosis could not be "
            "mapped to a numeric label."
        )

    return dataframe


def print_summary(
    split_name: str,
    dataframe: pd.DataFrame,
) -> None:
    """
    Print image, lesion and class counts.
    """

    print(f"\n{split_name}")
    print("-" * len(split_name))

    print(
        "Images:",
        len(dataframe),
    )

    print(
        "Unique lesions:",
        dataframe[
            "lesion_id"
        ].nunique(),
    )

    print(
        dataframe["dx"]
        .value_counts()
        .reindex(
            CLASS_NAMES,
            fill_value=0,
        )
    )


def main() -> None:
    ensure_output_directories()

    if not METADATA_CSV.exists():
        raise FileNotFoundError(
            f"Missing metadata file: "
            f"{METADATA_CSV}"
        )

    metadata = pd.read_csv(
        METADATA_CSV
    )

    validate_metadata(metadata)

    image_lookup = build_image_lookup(
        IMAGE_DIRS
    )

    metadata["image_path"] = (
        metadata["image_id"].map(
            image_lookup
        )
    )

    missing_images = metadata.loc[
        metadata["image_path"].isna(),
        "image_id",
    ].tolist()

    if missing_images:
        raise FileNotFoundError(
            f"{len(missing_images)} metadata "
            "images were not found. "
            f"Examples: {missing_images[:10]}"
        )

    # Create approximately 20% test data.
    remaining_dataframe, test_dataframe = (
        take_first_grouped_fold(
            dataframe=metadata,
            number_of_splits=5,
            random_seed=RANDOM_SEED,
        )
    )

    # Use approximately 20% of the
    # remaining data for validation.
    #
    # Approximate final percentages:
    # 64% training
    # 16% validation
    # 20% testing
    (
        training_dataframe,
        validation_dataframe,
    ) = take_first_grouped_fold(
        dataframe=remaining_dataframe,
        number_of_splits=5,
        random_seed=RANDOM_SEED + 1,
    )

    verify_no_lesion_leakage(
        training_dataframe,
        validation_dataframe,
        test_dataframe,
    )

    training_dataframe = add_numeric_labels(
        training_dataframe
    )

    validation_dataframe = add_numeric_labels(
        validation_dataframe
    )

    test_dataframe = add_numeric_labels(
        test_dataframe
    )

    preferred_columns = [
        "image_id",
        "lesion_id",
        "dx",
        "label",
        "image_path",
    ]

    other_columns = [
        column
        for column in metadata.columns
        if column not in preferred_columns
    ]

    output_columns = (
        preferred_columns
        + other_columns
    )

    training_dataframe[
        output_columns
    ].to_csv(
        TRAIN_CSV,
        index=False,
    )

    validation_dataframe[
        output_columns
    ].to_csv(
        VAL_CSV,
        index=False,
    )

    test_dataframe[
        output_columns
    ].to_csv(
        TEST_CSV,
        index=False,
    )

    print(
        "Split files saved in:",
        SPLIT_DIR,
    )

    print_summary(
        "TRAINING SET",
        training_dataframe,
    )

    print_summary(
        "VALIDATION SET",
        validation_dataframe,
    )

    print_summary(
        "TEST SET",
        test_dataframe,
    )

    print(
        "\nConfirmed: no lesion_id "
        "appears in more than one split."
    )


if __name__ == "__main__":
    main()