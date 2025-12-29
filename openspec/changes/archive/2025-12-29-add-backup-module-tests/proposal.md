## Change: Add focused tests for backup module orchestration

## Why
- `backup.py` is lightly covered and drives core Restic/Rsync orchestration; regressions risk data loss or skipped backups.
- Explicit tests will let us raise coverage while validating mount handling, command wiring, and maintenance hooks.

## What Changes
- Add pytest coverage for `Backup` flows (restic/rsync) using fakes for `DestinationHandler`, `Restic`, and `Rsync`.
- Exercise dry-run/happy-path branches, mask handling, and skip-maintain options without touching real disks.
- Introduce minimal seams if necessary for dependency injection to keep tests deterministic.

## Impact
- Affected specs: backup-testing
- Affected code: `src/bare/bare/backup.py`, new tests under `tests/`, minor seams/mocks for Restic/Rsync/DestinationHandler if needed.
