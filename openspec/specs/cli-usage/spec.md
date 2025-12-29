# cli-usage Specification

## Purpose
TBD - created by archiving change improve-bare-cli-ergonomics. Update Purpose after archive.
## Requirements
### Requirement: CLI help guides common workflows
The BARE CLI SHALL provide help text that makes common backup and maintenance workflows discoverable, including concise command descriptions and runnable examples for each subcommand.

#### Scenario: Root help summarizes commands and examples
- **WHEN** a user runs `bare --help`
- **THEN** the output lists available subcommands (backup, restic, umount, list) with one-line descriptions and includes at least one example showing how to run a backup with a session file

#### Scenario: Command help shows flags and examples
- **WHEN** a user runs `bare backup --help` or `bare restic --help`
- **THEN** the output documents required inputs, ergonomic flags (e.g., session path, dry-run/yes), and a copy-pastable example that reflects the recommended invocation

### Requirement: Session discovery is explicit and actionable
The BARE CLI SHALL resolve a default session file path when none is provided, announce the resolved path, and emit actionable errors when the session file is missing or unreadable.

#### Scenario: Default session path announced
- **WHEN** a user runs `bare backup` without a session path and the default `~/.config/bare/session.yml` exists
- **THEN** the CLI resolves the absolute path and logs which session file will be used before starting backups

#### Scenario: Missing session file gives guidance
- **WHEN** a user runs any command that requires a session file and the default or provided path does not exist
- **THEN** the CLI exits non-zero with an error that names the missing path and instructs the user to create it or pass an alternate via `--session` or an environment variable

### Requirement: Preflight checks and ergonomic safeguards
The BARE CLI SHALL perform preflight checks for required binaries/configuration and provide safeguards such as dry-run and confirmation to prevent accidental writes.

#### Scenario: Dependency preflight prevents execution
- **WHEN** a user runs `bare backup` and required binaries (e.g., restic, rsync, rclone, gocryptfs when enabled) are not available in PATH or configured paths
- **THEN** the CLI fails fast before starting backups, listing which dependencies are missing and how to install or configure them

#### Scenario: Dry-run shows planned actions without running backups
- **WHEN** a user runs `bare backup --dry-run`
- **THEN** the CLI prints the planned sources, destination, selected engines (restic/rsync), and mount actions, and exits without invoking restic or rsync

#### Scenario: Confirmation guard avoids accidental backups
- **WHEN** a user runs `bare backup` without `--yes` or a non-interactive override
- **THEN** the CLI prompts for confirmation showing the destination label/remote and aborts unless the user explicitly continues, while `--yes` skips the prompt for automation

### Requirement: Shortcut commands for frequent restic/rsync operations
The BARE CLI SHALL offer shortcut subcommands/flags for the most common restic and rsync operations so users do not have to remember full command strings.

#### Scenario: Snapshots shortcut lists repositories quickly
- **WHEN** a user runs `bare snapshots` or `bare restic --snapshots`
- **THEN** the CLI resolves the session file, runs `restic snapshots` for each configured repository, and prints the results without requiring the user to type the full restic command

#### Scenario: Common restic/rsync shortcuts are documented and runnable
- **WHEN** a user runs `bare restic --help` or `bare rsync --help`
- **THEN** the help output lists the available shortcuts (e.g., snapshots, stats/check/verify) with one-line descriptions and examples showing how to run them directly

### Requirement: CLI main module is self-documented for maintainers
The BARE CLI main entrypoint SHALL include module- and function-level documentation that explains command dispatch, session resolution, dependency checks, and shortcut handling so contributors can reason about CLI flows without external references, using numpydoc-style docstrings for functions.

#### Scenario: Core command handlers are documented
- **WHEN** a contributor reads `src/bare/main.py` to extend or debug CLI behavior
- **THEN** the module and key functions (parser construction, session resolution, config building, backup/restic/maintain/umount/list dispatch) include numpydoc-style docstrings describing purpose, inputs/outputs, and notable side effects such as confirmation/dry-run prompts.

#### Scenario: Inline notes cover safety checks and defaults
- **WHEN** a contributor reviews code paths for dependency preflight, default session resolution, and shortcut routing
- **THEN** inline comments or docstrings call out these safeguards and default behaviors so they are preserved during future changes, following concise numpydoc guidance (e.g., Parameters/Returns/Notes for side effects).
