## 1. Preparation
- [x] 1.1 Review `src/bare/mount` behaviors and external dependencies to define isolation seams.
- [x] 1.2 Add shared test fixtures/mocks for `DeviceFinder`, `execute_command`, platform detection, and temp directory handling.

## 2. Unit tests
- [x] 2.1 Add tests for `MountBase` covering temp directory creation, cleanup rules, and device lookup validation.
- [x] 2.2 Add tests for `MountDrive` dispatching between rclone and physical mount/unmount flows.
- [x] 2.3 Add tests for `MountDrivePhysical` OS selection, mount/unmount path resolution, and cleanup.
- [x] 2.4 Add tests for `MountDriveRclone` covering mount/unmount command invocation and temp directory cleanup.
- [x] 2.5 Add tests for `MountGocryptfs` covering valid repo mounts, invalid repo handling, and unmount cleanup.

## 3. Validation
- [x] 3.1 Run pytest for mount test suite and address failures.
- [x] 3.2 Run lint/format (Ruff) if code/test changes require it.
