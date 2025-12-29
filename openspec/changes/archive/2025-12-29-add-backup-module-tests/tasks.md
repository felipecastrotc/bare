## 1. Prep
- [x] 1.1 Review `backup.py` flows and identify seams for stubbing Restic/Rsync/DestinationHandler.

## 2. Tests
- [x] 2.1 Add tests for dry-run path (no external calls).
- [x] 2.2 Add tests for restic happy path with mask/args propagation.
- [x] 2.3 Add tests for rsync path and skip-maintain behavior.
- [x] 2.4 Add tests for error handling (missing destination/vol_label).

## 3. Validation
- [x] 3.1 Run `pixi run coverage` to ensure coverage rises and tests pass.
- [x] 3.2 Run `openspec validate add-backup-module-tests --strict`.
