# Contributing to BARE

Thank you for considering contributing!

## Development Setup

1. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```
2. Run code quality checks:
   ```bash
   pre-commit run --all-files
   ```
3. Run tests:
   ```bash
   pytest
   ```

## Workflow

- Fork the repository and create your branch from `main`.
- Ensure pre-commit hooks and tests pass before submitting a pull request.
- Describe your changes and include relevant tests.
