## 1. Baseline and targets
- [ ] 1.1 Capture current coverage report (line/branch) and identify top gaps by module/function.
- [ ] 1.2 Define targeted modules to lift (main orchestration, mount manager, finders, utils, backup/restic/rsync wrappers, destination handler).

## 2. Test implementation
- [ ] 2.1 Add tests for `mount_manager` covering mount/unmount sequencing and error handling with stubs.
- [ ] 2.2 Add tests for finder layers (`DeviceFinder`, physical/rclone/gocryptfs finders) with synthetic device listings.
- [ ] 2.3 Add tests for `destination_handler` and config/CLI helpers in `main.py` (session resolution, dependency checks, dry-run/yes logic) using mocks.
- [ ] 2.4 Add tests for backup/restic/rsync wrappers ensuring command construction/env handling.
- [ ] 2.5 Add tests for `utils` helpers (dict2args, modify_command_for_os, parse_mount) and any remaining low-coverage helpers.
- [ ] 2.6 Introduce minimal seams/refactors only if needed for testability (no behavior change).

## 3. Validation
- [ ] 3.1 Run `pixi run coverage` to confirm >=80% line coverage on `src/bare` with passing tests.
- [ ] 3.2 Run `openspec validate raise-coverage-to-80 --strict`.
