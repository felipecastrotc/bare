# Contributing to BARE

Thank you for considering contributing!

## Development Setup

This project uses [Pixi](https://pixi.sh/) as the environment manager. All development tools are managed via `pyproject.toml`.

### 1. Install Pixi

Follow instructions at [https://pixi.sh/](https://pixi.sh/) to install Pixi on your system.

### 2. Create the development environment

From the project root:

```bash
pixi install
```

This will create and populate a reproducible environment with all `dev` dependencies (e.g. `pytest`, `mypy`, `ruff`, etc).

### 3. Activate the environment

```bash
pixi shell
```

Pixi will drop you into a shell where all tools are available.

---

## Development Tasks

The most common tasks are predefined as [Pixi tasks](https://pixi.sh/docs/tasks/). You can run them via:

```bash
pixi run <task>
```

### Examples:

* **Run tests**

```bash
pixi run tests
```

* **Run pre-commit hooks manually**

```bash
pixi run precommit-run
```

* **Update all pre-commit hooks**

```bash
pixi run precommit-update
```

* **Type check with mypy**

```bash
mypy src
```

---

## Workflow

* Fork the repository and create your branch from `main`.
* Ensure all code passes:

  * pre-commit checks
  * mypy type checks
  * tests
* Submit a pull request with a clear description of your changes.

---

## Useful Notes

* The project uses `hatchling` for builds and versioning via Git tags (`hatch-vcs`).
* CI uses `pytest --cov`, `pre-commit`, and `mypy` for verification.
* Docs are managed via `mkdocs`, and are deployed from `main`.

---

## Code Formatting & Style

* Linting and formatting are enforced via `ruff`.
* Please run `pixi run precommit-run` before submitting a PR.
* Type annotations are expected in new or updated functions.

---

Thank you for contributing!
