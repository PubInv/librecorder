Software Framework

# Setup:
1. Install Conda from https://docs.conda.io/en/latest/miniconda.html (We can do a different package manager if needed).
2. Create a new environment from the environment.yml file:
   ```
   conda env create -f environment.yml
   ```
3. Activate the environment:
    ```
    conda activate myenv
    ```

# Usage:
1. Start the main application:
    ```
    python main.py
    ```
2. Upload an image:
    In a new terminal, run:
    ```
    python upload_image.py
    ```
    Select an image file from your local system.

This will automatically process the image and display the results (simple image mean for now).