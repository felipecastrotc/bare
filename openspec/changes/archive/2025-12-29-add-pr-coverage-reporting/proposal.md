## Change: Add PR coverage reporting and easy local coverage checks

## Why
- We currently run tests without surfacing coverage in pull requests, so reviewers can’t see how changes impact coverage or enforce minimum levels.
- Local coverage is ad-hoc and misconfigured (`your_package` placeholder), making it harder for contributors to measure gaps before opening PRs.

## What Changes
- Configure pytest-cov/coverage.py to target `src/bare`, emit XML/HTML/term-missing reports, and set a minimum coverage threshold.
- Add a Pixi task (and doc note) that runs coverage in one step for contributors and produces an HTML report for inspection.
- Update the PR CI workflow to run coverage, fail when below the threshold, and surface a PR-visible summary (status check and/or comment) plus an artifact for drill-down.

## Impact
- Affected specs: coverage-reporting
- Affected code: `pyproject.toml` coverage settings, Pixi tasks, CI workflow for tests/coverage, README/docs snippet for local coverage use.
