## ADDED Requirements
### Requirement: Project maintains >=80% coverage on core package
The codebase SHALL maintain at least 80% line coverage across `src/bare` when measured with pytest-cov in CI and local runs.

#### Scenario: Coverage threshold is achieved
- **WHEN** the test suite runs with pytest-cov targeting `src/bare`
- **THEN** the reported overall line coverage is at least 80%, matching the configured `fail_under` threshold

### Requirement: Critical orchestration paths are exercised by tests
The test suite SHALL cover primary orchestration paths and helpers so that configuration, mounting, and command execution flows are validated without relying on real devices.

#### Scenario: Mount manager and finder flows are covered
- **WHEN** tests run for mount management and device discovery
- **THEN** mount sequencing, unmount cleanup, and finder selection logic are exercised with stubs/mocks, contributing to the 80% coverage target

#### Scenario: Backup/restic/rsync command builders are covered
- **WHEN** tests run for backup orchestration and command wrappers
- **THEN** command construction, environment handling, and dry-run/confirmation logic are validated via mocks, increasing coverage on these modules toward the 80% goal

#### Scenario: Utility helpers are covered
- **WHEN** tests run for shared helpers (e.g., argument formatting, OS masking, mount parsing)
- **THEN** their branches are exercised and counted toward maintaining the >=80% coverage baseline
