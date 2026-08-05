from __future__ import annotations

import sys

import tensorflow as tf


def main() -> None:
    print("Python version:", sys.version)
    print("TensorFlow version:", tf.__version__)

    print(
        "Available devices:",
        tf.config.list_physical_devices(),
    )

    print(
        "Available GPUs:",
        tf.config.list_physical_devices("GPU"),
    )

    test_value = tf.reduce_sum(
        tf.random.normal([100, 100])
    )

    print(
        "TensorFlow test value:",
        float(test_value.numpy()),
    )

    print("TensorFlow installation is working.")


if __name__ == "__main__":
    main()