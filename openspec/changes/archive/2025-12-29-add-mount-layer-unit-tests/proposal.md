## Change: Add unit tests for mount layer modules

## Why
- Mount orchestration wraps platform-specific commands and external tools but currently lacks automated checks, making regressions around cleanup and OS branching easy to introduce.
- Adding targeted unit tests will let us validate mount/unmount flows without depending on real devices or binaries.

## What Changes
- Add pytest-based unit tests for `src/bare/mount/{base,drive,physical,rclone,gocryptfs}.py`, covering temporary directory handling, device discovery inputs, OS-specific dispatch, and cleanup behaviors.
- Mock external surfaces (e.g., `execute_command`, `platform.system`, `DeviceFinder`, `Gocryptfs`) and add minimal seams if needed to keep tests deterministic without real mounts.
- Capture expected mount/unmount outcomes for already-mounted cases versus fresh mounts to avoid false positives in CI.

## Impact
- Affected specs: mount-management
- Affected code: `src/bare/mount/*`, new/updated `tests/` for mount modules, shared test utilities used to stub command execution and platform detection.
