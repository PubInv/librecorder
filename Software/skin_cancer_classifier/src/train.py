from __future__ import annotations

import argparse
import json
import random

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

from sklearn.utils.class_weight import (
    compute_class_weight,
)

from .config import (
    CLASS_NAMES,
    MODEL_PATH,
    RANDOM_SEED,
    REPORT_DIR,
    TRAIN_CSV,
    TRAINING_LOG_PATH,
    VAL_CSV,
    ensure_output_directories,
)

from .data_pipeline import (
    build_dataset,
    read_split_csv,
)

from .model import (
    build_baseline_cnn,
)


def set_random_seeds(
    seed: int,
) -> None:
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def calculate_class_weights(
    labels: np.ndarray,
) -> dict[int, float]:
    """
    Give greater importance to
    underrepresented classes.
    """

    classes = np.arange(
        len(CLASS_NAMES)
    )

    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=labels,
    )

    return {
        int(class_index): float(weight)
        for class_index, weight
        in zip(classes, weights)
    }


def save_training_plots(
    history: tf.keras.callbacks.History,
) -> None:
    """
    Save training and validation graphs.
    """

    values = history.history

    plt.figure(figsize=(8, 5))

    plt.plot(
        values["accuracy"],
        label="Training accuracy",
    )

    plt.plot(
        values["val_accuracy"],
        label="Validation accuracy",
    )

    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")

    plt.title(
        "Training and Validation Accuracy"
    )

    plt.legend()
    plt.tight_layout()

    plt.savefig(
        REPORT_DIR
        / "training_accuracy.png",
        dpi=150,
    )

    plt.close()

    plt.figure(figsize=(8, 5))

    plt.plot(
        values["loss"],
        label="Training loss",
    )

    plt.plot(
        values["val_loss"],
        label="Validation loss",
    )

    plt.xlabel("Epoch")
    plt.ylabel("Loss")

    plt.title(
        "Training and Validation Loss"
    )

    plt.legend()
    plt.tight_layout()

    plt.savefig(
        REPORT_DIR
        / "training_loss.png",
        dpi=150,
    )

    plt.close()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train the HAM10000 CNN."
        )
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=30,
        help="Maximum number of epochs.",
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.001,
        help="Initial Adam learning rate.",
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    ensure_output_directories()

    set_random_seeds(
        RANDOM_SEED
    )

    training_dataframe = read_split_csv(
        TRAIN_CSV
    )

    validation_dataframe = read_split_csv(
        VAL_CSV
    )

    training_dataset = build_dataset(
        training_dataframe,
        training=True,
    )

    validation_dataset = build_dataset(
        validation_dataframe,
        training=False,
    )

    training_labels = (
        training_dataframe["label"]
        .astype("int32")
        .to_numpy()
    )

    class_weights = calculate_class_weights(
        training_labels
    )

    print("Class weights:")

    print(
        json.dumps(
            class_weights,
            indent=2,
        )
    )

    model = build_baseline_cnn()

    model.compile(
        optimizer=(
            tf.keras.optimizers.Adam(
                learning_rate=(
                    arguments.learning_rate
                )
            )
        ),

        loss=(
            tf.keras.losses
            .SparseCategoricalCrossentropy()
        ),

        metrics=[
            (
                tf.keras.metrics
                .SparseCategoricalAccuracy(
                    name="accuracy"
                )
            ),

            (
                tf.keras.metrics
                .SparseTopKCategoricalAccuracy(
                    k=2,
                    name="top_2_accuracy",
                )
            ),
        ],
    )

    model.summary()

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(MODEL_PATH),
            monitor="val_loss",
            save_best_only=True,
            verbose=1,
        ),

        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=6,
            restore_best_weights=True,
            verbose=1,
        ),

        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=0.000001,
            verbose=1,
        ),

        tf.keras.callbacks.CSVLogger(
            filename=str(
                TRAINING_LOG_PATH
            ),
        ),
    ]

    history = model.fit(
        training_dataset,

        validation_data=(
            validation_dataset
        ),

        epochs=arguments.epochs,

        class_weight=class_weights,

        callbacks=callbacks,
    )

    save_training_plots(
        history
    )

    print(
        "\nBest model saved to:",
        MODEL_PATH,
    )

    print(
        "Training log saved to:",
        TRAINING_LOG_PATH,
    )

    print(
        "Training graphs saved in:",
        REPORT_DIR,
    )


if __name__ == "__main__":
    main()