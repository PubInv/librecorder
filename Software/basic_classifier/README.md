# basic_classifier

Sample images and an early prototype classifier.

## Sample images

The `.jpeg` files in this folder (`image*`, `stomach_*`, `tongue_2_*`, `unirary_2_*`) are small sample images. They are useful for trying out the server, for example in the [setup guide](../../docs/setup.md#4-check-that-it-works).

## Prototype (`main.py`)

`main.py` is an early, standalone experiment that is **not** used by the web server. It classifies images by comparing their mean RGB colour to fixed per-class values (cardiac, stomach, tongue2, urinary2) and shows a confusion matrix.

It looks for one sub-folder per class in the current directory, so it is meant to be run from `urinary2/`, which contains `stomach/` and `tongue2/` folders and a copy of the script. It needs packages that are not in `requirements.txt`:

```
pip install opencv-python scikit-learn matplotlib
cd urinary2
python main.py
```

Classifiers used by the web server live in [`Software/processing/`](../processing/).
