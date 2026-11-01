# Using Librecorder for research

This guide is for researchers who want to use Librecorder to experiment. You would run your own model on your own images, compare approaches, and write up findings. 

You do **not** need to open a pull request, pass CI or follow the code review process to do any of this. That is only needed if you later want your model merged into Librecorder (see [CONTRIBUTING.md](../../CONTRIBUTING.md)).

## 1. Set up

Follow the [setup guide](../setup.md) to run the server locally.

## 2. Add your model as a local plugin

Librecorder runs any Python file in `Software/processing/` that defines `MODEL_ID`, `MODEL_NAME` and `run(image_path)` ([details](../architecture.md#classifier-plugins)). Create a file such as `Software/processing/my_experiment.py`:

```python
from PIL import Image
import numpy as np

MODEL_ID = "my_experiment_v1"      # unique; used to select the model
MODEL_NAME = "My experiment (v1)"  # shown in the dashboard

def run(image_path):
    img = np.array(Image.open(image_path).convert("RGB"), dtype=np.float32)
    score = float(img[..., 0].mean() / 255.0)   # replace with your model
    return {
        "classification": "High red" if score > 0.5 else "Low red",
        "confidence": round(abs(score - 0.5) * 2, 3),
    }
```

Refresh the dashboard (no restart needed) and your model appears in the model list. Don't commit your experiment file.

Tips:

- **Return `classification` (or `score`) plus `confidence` (0–1).** This matches the output standard being introduced for merged classifiers, so your plugin will not need rewriting if you contribute it later. You can return extra keys too.
- **Load heavy models lazily** (see `malaria_cnn.py`), so they load once per run rather than once per image.
- **Model not showing up?** It probably failed to import. Run `python -c "import my_experiment"` in `Software/processing/` to see the error.
- **Store model weights outside the repository folder**, so they can't be committed.

## 3. Load your images

Commands below are for Mac/Linux; on Windows, see the note in the [setup guide](../setup.md#4-check-that-it-works).

- **A few images:** upload them through the dashboard, or with `POST /upload`. Reuse the same `case_id` to put several images in one case:
  ```
  curl -F "file=@image.jpg" -F "case_id=my-dataset" http://127.0.0.1:8000/upload
  ```
- **A whole folder:** `POST /import_folder` copies `.jpg`, `.png` and `.tif` images from a folder on the server's machine into a case (new unless `case_id` is given):
  ```
  curl -X POST -H "Content-Type: application/json" \
       -d '{"src": "/absolute/path/to/images", "description": "my dataset"}' \
       http://127.0.0.1:8000/import_folder
  ```

## 4. Run your model and collect results

```
curl -X POST -H "Content-Type: application/json" \
     -d '{"case_id": "<case_id>", "model_id": "my_experiment_v1"}' \
     http://127.0.0.1:8000/run_model > results.json
```

Use the `case_id` returned by the upload or import step. The response contains a result for every image (`per_image`) and a summary (`aggregate`). **Save the response.** The server only stores the summary, so `results.json` is your record of per-image results.

## Data and licensing

- **Never commit datasets or patient images**; link to the dataset source instead. See the full list in [CONTRIBUTING.md](../../CONTRIBUTING.md#repository-rules).
- **Check your dataset's license.** Many medical imaging datasets (e.g. HAM10000, DDI) have their own terms, such as non-commercial use or a data-use agreement. Those terms apply to your data and, possibly, to models trained on it, independently of Librecorder's license.
- **Remove identifying details** (names, dates, faces) from patient images before uploading them, even to a local server.
- **Using Librecorder privately carries no obligations** under its AGPL-3.0 license. Obligations apply only if you distribute it or run a modified version as a service for others. See the full [LICENSE](../../LICENSE).

## Reports

<!-- TODO: where research and progress reports should live (this folder, a wiki, or elsewhere) is pending a team decision. Update this section once decided. -->

Put your report in this folder and add a row to the table.

| Report | Author | Date |
|---|---|---|
| [Literature review (draft)](postdoc_activities/Lit_Review_draft.pdf) | Avinash Baskaran et al. | May 2025 |
| [Postdoc report-out](postdoc_activities/Postdoc_Report_Out_5_12.pdf) | Avinash Baskaran | May 2025 |
| [HAM10000 / DDI / PanDerm classifier report](../../open-source-documentation-for-classifier-development.md) | Rudmila Nizam | Oct 2026 |
