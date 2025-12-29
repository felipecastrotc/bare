# coverage-reporting Specification

## Purpose
TBD - created by archiving change add-pr-coverage-reporting. Update Purpose after archive.
## Requirements
### Requirement: PRs enforce and display coverage status
The CI pipeline SHALL run tests with coverage for pull requests, enforce a minimum threshold, and surface the result to reviewers.

#### Scenario: Coverage threshold gates PR status
- **WHEN** a PR workflow runs tests
- **THEN** pytest-cov measures coverage on `src/bare`, the run fails if coverage is below the configured threshold, and the PR status check reflects the pass/fail result

#### Scenario: PRs show coverage summary to reviewers
- **WHEN** the coverage workflow finishes on a PR
- **THEN** the PR shows a summary (status description or comment) with line/branch coverage percentages and links to the uploaded report artifact

### Requirement: Contributors can run coverage locally with one command
The project SHALL provide a single documented command to run tests with coverage, emit human-friendly and machine-readable reports, and mirror CI settings.

#### Scenario: Local coverage command mirrors CI
- **WHEN** a contributor runs the documented coverage task (e.g., `pixi run coverage` or equivalent)
- **THEN** tests run with the same coverage config as CI, a terminal summary with missing lines/branches is shown, and XML + HTML reports are written to predictable paths for further inspection
