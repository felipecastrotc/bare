# BARE: Backup Automation with Replication and Encryption

**BARE** is a versatile backup solution written in Python, designed to handle automated backup tasks with replication and encryption using tools like Restic and Rsync. It provides a streamlined interface for backing up data to various destinations with support for both command-line configuration and YAML-based sessions. It currently supports Linux, macOS and Android (Termux).

## Features

- **Automated Backups**: Perform automated backups using Restic and Rsync.
- **Encryption Support**: Secure your backups with Restic's encryption capabilities.
- **Customizable Configurations**: Easily configure your backup sessions using YAML files.
- **Session Management**: Manage different backup sessions with ease.
- **Flexible Command Routing**: Use subcommands to run specific backup tasks, list configurations, or manage mount points.
- **Automatic Mounting**: Automatically mount and unmount volumes or rclone remotes by specifying the volume label or rclone name.
- **Cross-Platform Support**: Supports Linux and macOS.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/felipecastrotc/BARE.git
   cd BARE
   ```

2. Install the required dependencies:
   ```bash
   pip install .
   ```

3. Ensure that you have Restic and Rsync installed on your system:
   - [Restic Installation Guide](https://restic.readthedocs.io/en/stable/020_installation.html)
   - [Rsync Installation Guide](https://rsync.samba.org/download.html)

This will install the `bare` package along with its dependencies.


### Platform-Specific Instructions

- **Linux/Android**: All features, including masking and automatic mounting, work out of the box. However, for the masking functionality to work, you need to have `proot` installed.

   To install `proot` on Linux (Debian based):
   ```bash
   sudo apt-get install proot
   ```

   To install `proot` on Android (Termux):
   ```bash
   pkg install proot
   ```

- **macOS**: For masking functionality to work, you need to install [Rustic](https://github.com/rustic-rs/rustic), which is a Restic version written in Rust it has the mask functionality implemented natively.

   To install Rustic on macOS:
   ```bash
   cargo install rustic
   ```

## Usage

### Basic Commands

The main script provides several subcommands for managing backups, Restic commands, unmounting resources, and listing configurations.

#### 1. Backup

Perform a backup using the configuration provided in the `session.yml` file or command-line arguments.

```bash
bare backup
```

If the destination is specified as a volume label or an rclone name, BARE will automatically mount the volume or rclone remote before starting the backup and unmount it afterward.

#### 2. Restic

Run a Restic command against the configured backups without needing to manage the repository manually.

```bash
bare restic snapshots
```

#### 3. Umount

Unmount and clean up temporary folders used during the backup process.

```bash
bare umount
```

#### 4. List

List all available sessions and configurations defined in the session file.

```bash
bare list
```

### Configuration

BARE uses a YAML configuration file (`session.yml`) to define backup sessions. This file must be placed in the `~/.config/bare/` directory as `session.yml`. Below is a sample configuration:

```yaml
default:
  hostname: my-computer         # Optional: Override the default hostname with a custom one
  destination: my-volume-label  # Specify a path, volume label, or Restic rest-server
  source:                       # List of folders to back up
    - ~/Documents
    - ~/Pictures
  mask:                         # (Optional) Mask source paths; on Linux, proot is required, and on macOS, rustic is needed
    - /test/Documents
    - /test2/Pictures
  restic:
    password: mypassword
    enable: true
    args:                       # Additional arguments to pass to Restic
      exclude-file: "/path/to/my/ignore_file"
  rsync:
    enable: false               # Disable Rsync backup if not needed
```

In this example, the `destination` can be a filesystem path, volume label, or an rclone remote name. If a volume label or rclone name is specified, BARE will automatically handle the mounting and unmounting process. You can include multiple configurations within a single file, and BARE will sequentially process each one.

### Example Session

To create a custom session, create a `session.yml` file in your home directory under `~/.config/bare/` or pass it directly via the `--session` flag.

### Session Structure

- **hostname**: The name of the computer performing the backup.
- **destination**: The backup destination path, volume label, or rclone remote name.
- **source**: List of folders to back up.
- **mask**: List of masks for the folders to back up.
- **restic**: Configuration for Restic backup, including password and folder and extra arguments.
- **rsync**: Configuration for Rsync backup, if enabled.
- **check_hostname**: Boolean to validate the hostname during the backup.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub if you have suggestions, bug reports, or enhancements.

### Development

To maintain code quality, BARE uses `black` for code formatting. Please ensure that your code is formatted with `black` before submitting a pull request.

To format your code with `black`, install it using pip:

```bash
pip install black
```

Then, format your code by running:

```bash
black .
```

This will automatically format all Python files in the current directory to conform to the `black` code style.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
