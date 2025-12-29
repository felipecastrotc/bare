## Change: Add unit tests for main.py CLI orchestration

## Why
- `main.py` drives CLI parsing, session resolution, dependency checks, and dispatch; coverage is low and control flow is complex.
- Adding tests will reduce regressions in backup/restic/snapshots/maintain commands and error handling without requiring real sessions or binaries.

## What Changes
- Add pytest coverage for CLI helper functions and dispatch paths (backup, restic, snapshots, maintain, umount) using mocks for session loading, DestinationHandler, Restic, Rsync, and MountManager.
- Cover error paths (missing session, missing dependencies) and dry-run/assume-yes branches.
- Introduce minimal seams if needed to make dispatch testable (no behavior changes).

## Impact
- Affected specs: cli-main-testing
- Affected code: `src/bare/main.py` (tests under `tests/`), minor seams/mocks to enable deterministic dispatch testing.
