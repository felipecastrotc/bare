# cli-main-testing Specification

## Purpose
TBD - created by archiving change add-main-cli-tests. Update Purpose after archive.
## Requirements
### Requirement: CLI orchestration paths are covered by unit tests
The main CLI module SHALL be exercised by unit tests that cover dispatch branches, dependency checks, and error handling without invoking real backups.

#### Scenario: Parser and restic shortcuts are tested
- **WHEN** tests build the CLI parser and construct restic commands from flags
- **THEN** subcommands and shortcut resolution (snapshots/stats/check) are validated

#### Scenario: Session resolution and dependency failures are tested
- **WHEN** tests run session resolution and dependency checks
- **THEN** missing session/env/file errors and missing binary exits are exercised

#### Scenario: Command dispatch paths are tested
- **WHEN** tests invoke backup/restic/snapshots/maintain/umount dispatch with mocks
- **THEN** the appropriate handlers are called, dry-run/assume-yes branches are exercised, and no real mounts or binaries are used
