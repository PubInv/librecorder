# Contributing to Librecorder

Welcome. Librecorder is a [Public Invention](https://pubinv.org) project, run by volunteers. There are two ways to contribute:

- **With code**: backend changes, documentation, or ML classifiers. See: [architecture overview](docs/codebase/architecture.md).
- **With research**: using Librecorder to run experiments, and sharing your findings. See: [research guide](docs/research/README.md).

## Making a change

1. **Fork & clone** this repository. 
2. **Set up:**
   ```bash
   pip install -r requirements.txt
   ```
   See also: [setup guide](docs/setup.md).
3. **Branch:**
   ```bash
   git checkout -b your-change-name
   ```
4. **Open a pull request** against `main` with a description of what changed and why.

<!-- TODO: mention PR templates here once .github/ templates exist. -->

### Merging classifiers

A classifier is a single Python file loaded by the server. See [Classifier plugins](docs/codebase/architecture.md#classifier-plugins) for how they are discovered and run. Before opening a classifier PR, check that:

- It is in `Software/processing/`, with a `MODEL_ID`, `MODEL_NAME` and a `run(image_path)` function.
- Its code is compatible with AGPL-3.0, and any third-party code keeps its original license notice.

Automated checks and a standard output format (issues #37 and #40) for classifier PRs are coming soon.
<!-- TODO: merge format_output.py, add "passes the contract tests" with the command to run them locally, once the CI checks exist. -->

## Repository rules 

**Documentation:** 
- For server-level changes, update the setup guide in [`setup.md`](docs/setup.md). If you added any additional dependencies, update the [`requirements.txt`](requirements.txt) too.
- For code changes, update the architecture in [`codebase/architecture.md`](docs/codebase/architecture.md).
- For research updates, add them to the index at [`research/README.md`](docs/research/README.md).

**Never commit:**
- Changes to databases (`*.db`, including `instance/`) or `__pycache__/*.pyc` files (running the server modifies these; see [setup](docs/setup.md#things-to-know))
- `.env` files, passwords, API keys or other credentials
- Patient or case images, uploaded case files (`uploads/`), datasets, or any personal data
- Model weights or other large binary files

---

**Need help?** Open a [GitHub issue](https://github.com/PubInv/librecorder/issues).

**Want to join Public Invention?** Follow the instructions at [pubinv.org/volunteer](https://www.pubinv.org/volunteer/).

**Licensing:** *By contributing, you agree that your work is licensed under [AGPL-3.0](LICENSE).*