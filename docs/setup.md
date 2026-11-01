# Setup guide

This guide gets the Librecorder web server running locally on your own computer. 

Setup instructions are the same for both code contributors and researchers.

## Prerequisites

Please ensure you have git and Python 3.12 or newer installed (tested with 3.12 and 3.14).

To check your version, open your terminal and run these commands: 
- `git --version`
- `python --version` for Windows, `python3 --version` for Mac/Linux. 

If needed, refer to the official [git](https://www.git-scm.com/downloads) and [Python](https://www.python.org/downloads/) installation docs. On Windows, tick **"Add python.exe to PATH"** in the Python installer.

## Setting up the server

### 1. Get the code

Download the code and move into the folder it creates.

```
git clone https://github.com/PubInv/librecorder.git
cd librecorder
```

### 2. Create an environment and install dependencies

All server dependencies are listed in [`requirements.txt`](../requirements.txt) in the repository root. Pick **one** of the options below.

#### Option A: venv (recommended)

Mac/Linux:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (Command Prompt):
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

In PowerShell, use `.venv\Scripts\Activate.ps1`. If you get a script execution error, use Command Prompt instead.

#### Option B: conda

```
conda create -y -n librecorder-web python=3.12
conda activate librecorder-web
pip install -r requirements.txt
```

> **Note:** `environment.yml` in the repository root is **not** the web server environment. It is a Windows/CUDA export of the training environment for `Software/malaria_classifier/`, and it is missing `flask-cors` and `flask-sqlalchemy`, so the server won't start from it.

#### Optional extras

| Package | Needed for |
|---|---|
| `torch` | The malaria classifier (`Software/processing/malaria_cnn.py`). Without it, that model simply does not appear in the model list. |
| `requests` | The desktop upload client `Software/WebApp/upload_pic.py`. It also needs tkinter, which some Linux systems lack (install with `sudo apt install python3-tk`). |

Install them with `pip install torch` / `pip install requests`.

### 3. Run the server

```
cd Software/WebApp
python app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) once you see `Running on http://127.0.0.1:8000`. You should see the Librecorder dashboard. Use `http://`, not `https://`. Press `Ctrl+C` to stop the server.

**Warning:** the server listens on all network interfaces (`0.0.0.0`) and has no login, so anyone on your network can reach it. Only run it on networks you trust.

### 4. Check that it works

From the dashboard you can upload images and run a model. To check from the command line instead, leave the server running. Open a second terminal and `cd` back to the `librecorder` folder, then run (Mac/Linux shown):

```
# 1. List the available models
curl http://127.0.0.1:8000/models

# 2. Upload a sample image (creates a new case and prints its case_id)
curl -F "file=@Software/basic_classifier/stomach_1.jpeg" http://127.0.0.1:8000/upload

# 3. Run a model on that case (replace <case_id>)
curl -X POST -H "Content-Type: application/json" \
     -d '{"case_id": "<case_id>", "model_id": "dark_light_v1"}' \
     http://127.0.0.1:8000/run_model

# 4. Read the stored result
curl http://127.0.0.1:8000/results/<case_id>

# 5. Delete the test case
curl -X DELETE http://127.0.0.1:8000/purge/<case_id>
```

Step 1 should list at least `dark_light_v1` and `mean_pixel_v1` (plus `malaria_cnn_v1` if torch is installed).

On Windows, use Command Prompt (not PowerShell) for these checks. Steps 1, 2, 4 and 5 work as written; step 3 must be on one line with escaped quotes:

```
curl -X POST -H "Content-Type: application/json" -d "{\"case_id\": \"<case_id>\", \"model_id\": \"dark_light_v1\"}" http://127.0.0.1:8000/run_model
```

## Things to know

- **Using the server changes tracked files.** Uploading or running models modifies the database `Software/WebApp/openlims.db`, and Python may modify or add `__pycache__/*.pyc` files. Do not commit those changes. Undo them with:
  ```
  git restore Software/WebApp/openlims.db Software/WebApp/__pycache__ Software/processing/__pycache__
  ```
  and delete any new, untracked `__pycache__` files that `git status` shows.
- **Uploads are stored on disk** in `Software/WebApp/uploads/<case_id>/`.
- **`upload_pic.py` talks to the live server** (`microlab.parccommons.org`), not your local one. Change `SERVER` at the top of the file to `http://127.0.0.1:8000` to use it locally.

## Next steps
Now that you have the server running locally on your computer, you can begin contributing.
- See how the pieces fit together: [architecture.md](architecture.md)
- Start experimenting with your own model or data: [research guide](research/README.md)
- Review the rules for contributing code: [CONTRIBUTING.md](../CONTRIBUTING.md)
