from __future__ import annotations

from pathlib import Path


# Root of the classifier project
PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Dataset folders
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
SPLIT_DIR = PROJECT_ROOT / "data" / "splits"


# Output folders
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"
REPORT_DIR = PROJECT_ROOT / "reports"


# HAM10000 metadata file
METADATA_CSV = (
    RAW_DATA_DIR / "HAM10000_metadata.csv"
)


# HAM10000 image folders
IMAGE_DIRS = (
    RAW_DATA_DIR / "HAM10000_images_part_1",
    RAW_DATA_DIR / "HAM10000_images_part_2",
)


# Generated train, validation and test CSVs
TRAIN_CSV = SPLIT_DIR / "train.csv"
VAL_CSV = SPLIT_DIR / "val.csv"
TEST_CSV = SPLIT_DIR / "test.csv"


# Generated model
MODEL_PATH = (
    ARTIFACT_DIR / "best_model.keras"
)

TRAINING_LOG_PATH = (
    ARTIFACT_DIR / "training_log.csv"
)


# Image configuration
IMAGE_SIZE = 128
BATCH_SIZE = 32


# Used to make splitting and training reproducible
RANDOM_SEED = 42


# Fixed label order
CLASS_NAMES = [
    "akiec",
    "bcc",
    "bkl",
    "df",
    "mel",
    "nv",
    "vasc",
]


CLASS_DESCRIPTIONS = {
    "akiec": (
        "Actinic keratoses / "
        "intraepithelial carcinoma"
    ),
    "bcc": "Basal cell carcinoma",
    "bkl": "Benign keratosis-like lesions",
    "df": "Dermatofibroma",
    "mel": "Melanoma",
    "nv": "Melanocytic nevi",
    "vasc": "Vascular lesions",
}


LABEL_TO_INDEX = {
    class_name: index
    for index, class_name
    in enumerate(CLASS_NAMES)
}


INDEX_TO_LABEL = {
    index: class_name
    for class_name, index
    in LABEL_TO_INDEX.items()
}


def ensure_output_directories() -> None:
    """
    Create folders used for generated output.
    """

    for directory in (
        SPLIT_DIR,
        ARTIFACT_DIR,
        REPORT_DIR,
    ):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )