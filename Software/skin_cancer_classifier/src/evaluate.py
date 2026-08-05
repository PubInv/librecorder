from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)

from .config import (
    CLASS_DESCRIPTIONS,
    CLASS_NAMES,
    MODEL_PATH,
    REPORT_DIR,
    TEST_CSV,
    ensure_output_directories,
)

from .data_pipeline import (
    build_dataset,
    read_split_csv,
)


def save_confusion_matrix(
    matrix: np.ndarray,
) -> None:
    figure, axis = plt.subplots(
        figsize=(9, 8)
    )

    image = axis.imshow(matrix)

    axis.set_title(
        "HAM10000 Confusion Matrix"
    )

    axis.set_xlabel(
        "Predicted class"
    )

    axis.set_ylabel(
        "True class"
    )

    axis.set_xticks(
        range(len(CLASS_NAMES))
    )

    axis.set_yticks(
        range(len(CLASS_NAMES))
    )

    axis.set_xticklabels(
        CLASS_NAMES,
        rotation=45,
        ha="right",
    )

    axis.set_yticklabels(
        CLASS_NAMES
    )

    threshold = (
        matrix.max() / 2
        if matrix.size
        else 0
    )

    for row_index in range(
        matrix.shape[0]
    ):
        for column_index in range(
            matrix.shape[1]
        ):
            value = matrix[
                row_index,
                column_index,
            ]

            axis.text(
                column_index,
                row_index,
                str(value),
                ha="center",
                va="center",

                color=(
                    "white"
                    if value > threshold
                    else "black"
                ),
            )

    figure.colorbar(
        image,
        ax=axis,
    )

    figure.tight_layout()

    figure.savefig(
        REPORT_DIR
        / "confusion_matrix.png",
        dpi=150,
    )

    plt.close(figure)


def calculate_per_class_metrics(
    matrix: np.ndarray,
    report: dict,
) -> pd.DataFrame:
    rows: list[dict] = []

    total = float(
        matrix.sum()
    )

    for class_index, class_name in enumerate(
        CLASS_NAMES
    ):
        true_positive = float(
            matrix[
                class_index,
                class_index,
            ]
        )

        false_negative = float(
            matrix[
                class_index,
                :,
            ].sum()
            - true_positive
        )

        false_positive = float(
            matrix[
                :,
                class_index,
            ].sum()
            - true_positive
        )

        true_negative = (
            total
            - true_positive
            - false_negative
            - false_positive
        )

        sensitivity = (
            true_positive
            / (
                true_positive
                + false_negative
            )
            if (
                true_positive
                + false_negative
            ) > 0
            else 0.0
        )

        specificity = (
            true_negative
            / (
                true_negative
                + false_positive
            )
            if (
                true_negative
                + false_positive
            ) > 0
            else 0.0
        )

        rows.append(
            {
                "class": class_name,

                "description": (
                    CLASS_DESCRIPTIONS[
                        class_name
                    ]
                ),

                "precision": float(
                    report[
                        class_name
                    ]["precision"]
                ),

                "sensitivity_recall": (
                    sensitivity
                ),

                "specificity": specificity,

                "f1_score": float(
                    report[
                        class_name
                    ]["f1-score"]
                ),

                "support": int(
                    report[
                        class_name
                    ]["support"]
                ),
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    ensure_output_directories()

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: "
            f"{MODEL_PATH}"
        )

    test_dataframe = read_split_csv(
        TEST_CSV
    )

    test_dataset = build_dataset(
        test_dataframe,
        training=False,
    )

    model = tf.keras.models.load_model(
        MODEL_PATH
    )

    probabilities = model.predict(
        test_dataset,
        verbose=1,
    )

    predicted_labels = np.argmax(
        probabilities,
        axis=1,
    )

    true_labels = (
        test_dataframe["label"]
        .astype("int32")
        .to_numpy()
    )

    report_dictionary = classification_report(
        true_labels,
        predicted_labels,

        labels=np.arange(
            len(CLASS_NAMES)
        ),

        target_names=CLASS_NAMES,

        output_dict=True,

        zero_division=0,
    )

    report_text = classification_report(
        true_labels,
        predicted_labels,

        labels=np.arange(
            len(CLASS_NAMES)
        ),

        target_names=CLASS_NAMES,

        zero_division=0,
    )

    one_hot_true_labels = (
        tf.keras.utils.to_categorical(
            true_labels,

            num_classes=(
                len(CLASS_NAMES)
            ),
        )
    )

    try:
        macro_roc_auc = float(
            roc_auc_score(
                one_hot_true_labels,
                probabilities,
                average="macro",
                multi_class="ovr",
            )
        )

    except ValueError:
        macro_roc_auc = float("nan")

    overall_metrics = {
        "accuracy": float(
            accuracy_score(
                true_labels,
                predicted_labels,
            )
        ),

        "balanced_accuracy": float(
            balanced_accuracy_score(
                true_labels,
                predicted_labels,
            )
        ),

        "macro_f1": float(
            f1_score(
                true_labels,
                predicted_labels,
                average="macro",
            )
        ),

        "weighted_f1": float(
            f1_score(
                true_labels,
                predicted_labels,
                average="weighted",
            )
        ),

        "macro_roc_auc_ovr": (
            macro_roc_auc
        ),
    }

    matrix = confusion_matrix(
        true_labels,
        predicted_labels,

        labels=np.arange(
            len(CLASS_NAMES)
        ),
    )

    per_class_metrics = (
        calculate_per_class_metrics(
            matrix,
            report_dictionary,
        )
    )

    (
        REPORT_DIR
        / "classification_report.txt"
    ).write_text(
        report_text,
        encoding="utf-8",
    )

    pd.DataFrame(
        report_dictionary
    ).transpose().to_csv(
        REPORT_DIR
        / "classification_report.csv"
    )

    per_class_metrics.to_csv(
        REPORT_DIR
        / "per_class_metrics.csv",
        index=False,
    )

    (
        REPORT_DIR
        / "test_metrics.json"
    ).write_text(
        json.dumps(
            overall_metrics,
            indent=2,
        ),
        encoding="utf-8",
    )

    save_confusion_matrix(
        matrix
    )

    prediction_results = (
        test_dataframe[
            [
                "image_id",
                "lesion_id",
                "dx",
                "image_path",
            ]
        ].copy()
    )

    prediction_results[
        "predicted_dx"
    ] = [
        CLASS_NAMES[index]
        for index in predicted_labels
    ]

    prediction_results[
        "confidence"
    ] = probabilities.max(axis=1)

    for class_index, class_name in enumerate(
        CLASS_NAMES
    ):
        prediction_results[
            f"probability_{class_name}"
        ] = probabilities[
            :,
            class_index,
        ]

    prediction_results.to_csv(
        REPORT_DIR
        / "test_predictions.csv",
        index=False,
    )

    print(report_text)

    print(
        "\nPer-class medical metrics:"
    )

    print(
        per_class_metrics.to_string(
            index=False
        )
    )

    print("\nOverall metrics:")

    print(
        json.dumps(
            overall_metrics,
            indent=2,
        )
    )

    print(
        "\nReports saved in:",
        REPORT_DIR,
    )


if __name__ == "__main__":
    main()