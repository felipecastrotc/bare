## ADDED Requirements
### Requirement: Temporary mount directories are isolated and cleaned
The mount layer SHALL create temporary mount directories with restrictive permissions and remove them when they are mount-layer artifacts.

#### Scenario: Temporary directories use mount prefix and secure permissions
- **WHEN** a mount helper requests a temporary directory for mounts or symlink placeholders
- **THEN** the directory is created with a `BUP.tmp.` prefix, user-only permissions, and is removed immediately when only a name is needed

#### Scenario: Temporary paths are cleaned during unmount
- **WHEN** unmount logic receives a device or path that includes the temporary prefix and the path exists
- **THEN** the directory is removed after unmounting, and calls without a device or path raise a validation error

### Requirement: Mount dispatch selects backend by filesystem type
The mount orchestrator SHALL route mount/unmount calls to the rclone backend for rclone filesystems and to the physical backend for others.

#### Scenario: rclone devices use the rclone backend
- **WHEN** a device reports `fstype` of `fuse.rclone`
- **THEN** mount/unmount calls are delegated to the rclone backend and raise an error if the device cannot be found

#### Scenario: non-rclone devices use the physical backend
- **WHEN** a device reports any other filesystem type
- **THEN** mount/unmount calls are delegated to the physical backend using the located device by label or name

### Requirement: Physical drive mounting respects OS handlers and avoids redundant work
Physical mount helpers SHALL select platform-specific commands, skip already-mounted drives, and clean temporary paths after unmount.

#### Scenario: Unmounted drive mounts via OS-specific helper
- **WHEN** a device has no mountpoints and the platform is Linux or Darwin
- **THEN** the corresponding helper (`udisksctl` or `diskutil`) is invoked and the call returns True to signal a new mount

#### Scenario: Unmount resolves path and cleans temp directories
- **WHEN** unmount is requested without a path but the device has mountpoints
- **THEN** the first mountpoint is used, the OS helper unmounts it, temporary directories are removed, and requests without any identifiers raise a validation error

### Requirement: Rclone mounts use temporary directories and enforce OS support
Rclone mount helpers SHALL mount to freshly created temporary directories, refuse unsupported OSes, and clean up after unmount.

#### Scenario: Fresh mount creates temp dir and runs rclone
- **WHEN** an rclone-labeled device has no existing mountpoints
- **THEN** a temporary directory is created, `rclone mount ... --daemon` is invoked against it, and the call returns True; already-mounted devices log and return False

#### Scenario: Unmount uses system umount on supported OSes
- **WHEN** unmount is requested on Linux or Darwin
- **THEN** `umount` is invoked for the mountpoint, the temporary directory is removed, and unsupported platforms raise a not-implemented error

### Requirement: Gocryptfs mounts validate repositories before attaching
Gocryptfs helpers SHALL verify encrypted repositories before mounting, use temporary directories for mounts, and clean up after unmount.

#### Scenario: Valid repository mounts to temp directory
- **WHEN** the target path passes `gocryptfs -info` and is not currently mounted
- **THEN** a temporary directory is created, the repository is mounted there, and the call returns True; already-mounted repos log and return False

#### Scenario: Invalid repository is rejected without mounting
- **WHEN** `gocryptfs -info` fails
- **THEN** the helper logs the failure and returns False without attempting to mount

#### Scenario: Unmount cleans temporary directories on supported OSes
- **WHEN** unmount is requested on Linux or Darwin with a known mountpoint
- **THEN** `umount` is invoked for the target path, temporary directories with the mount prefix are removed, and unsupported platforms raise a not-implemented error
