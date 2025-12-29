## 1. Prep
- [x] 1.1 Identify main.py dispatch branches to cover (backup/restic/snapshots/maintain/umount, dependency failures, missing session).

## 2. Tests
- [x] 2.1 Add tests for parser construction and restic shortcut command building.
- [x] 2.2 Add tests for session resolution/load error paths and dependency failure exit.
- [x] 2.3 Add tests for backup/restic/snapshots/maintain dispatch using mocks for DestinationHandler/Restic/Rsync/MountManager.
- [x] 2.4 Add tests for dry-run/assume-yes branches to avoid real execution.

## 3. Validation
- [ ] 3.1 Run `pixi run coverage` to confirm coverage increases and gate passes.
- [ ] 3.2 Run `openspec validate add-main-cli-tests --strict`.
