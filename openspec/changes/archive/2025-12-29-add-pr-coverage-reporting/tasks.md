## 1. Coverage configuration
- [x] 1.1 Align coverage source/omit settings in `pyproject.toml` (remove `your_package`, target `src/bare`, enable XML + HTML + term-missing).
- [x] 1.2 Add/update Pixi task to run coverage in one step and write reports to a predictable location (e.g., `coverage.xml`, `htmlcov/`).
- [x] 1.3 Document the local coverage command in README/CONTRIBUTING for contributors.

## 2. CI integration
- [x] 2.1 Update the PR test workflow to run coverage with pytest-cov and enforce a minimum threshold (fail status below threshold).
- [x] 2.2 Publish coverage summary to PRs (status and/or comment) and upload HTML/LCOV artifact for drill-down.

## 3. Validation
- [x] 3.1 Run `openspec validate add-pr-coverage-reporting --strict`.
- [x] 3.2 Exercise the coverage task locally (or in CI) to confirm reports generate and thresholds behave as expected.
