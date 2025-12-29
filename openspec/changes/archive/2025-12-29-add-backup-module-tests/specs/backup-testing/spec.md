## ADDED Requirements
### Requirement: Backup orchestration is covered by unit tests
The backup module SHALL be validated by unit tests that exercise restic and rsync orchestration without real mounts.

#### Scenario: Dry-run and missing destination are tested
- **WHEN** tests run the backup module in dry-run or with missing destination/volume inputs
- **THEN** dry-run avoids external calls, and invalid configurations raise errors as expected

#### Scenario: Restic backup flow is tested
- **WHEN** tests invoke restic backups with masks/args
- **THEN** DestinationHandler context, Restic invocation, and skip-maintain options are exercised via stubs

#### Scenario: Rsync backup flow is tested
- **WHEN** tests invoke rsync backups
- **THEN** command construction and destination handling are exercised via stubs without touching real disks
