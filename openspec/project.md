# Project Context

## Purpose
BARE is a Python CLI that automates backups across Linux, macOS, Android/Termux (Windows support is aspirational). It reads a YAML session file or CLI flags to orchestrate mounting destinations (physical drives by label, rclone remotes, optional gocryptfs layers) and runs Restic or Rsync jobs, then cleans up mounts. The goal is to make repeatable, encrypted backups easy with minimal setup and safe defaults.

## Tech Stack
- Python 3.10+ (targets 3.12), standard library first with a single runtime dependency on `pyyaml`
- CLI entrypoints via `bare` / `bare_runner` console scripts (Hatch build system)
- External binaries: `restic`, `rsync`, `rclone`, `gocryptfs` (optional), `proot` on Android/Termux, `rustic` for macOS masking
- Documentation via MkDocs; lint/format/type-check with Ruff + mypy; pytest/coverage available for tests

## Project Conventions

### Code Style
- Ruff formatter with 88-char lines, double quotes, and import ordering (`pyproject.toml` defines rules); ignore long-line warning `E501`
- Prefer type annotations everywhere; mypy runs in strict mode
- Keep dependencies minimal and favor stdlib; short, focused functions; small files
- Pre-commit is available; run Ruff (`ruff check . --fix`, `ruff format .`) before commits

### Architecture Patterns
- Thin CLI in `src/bare/main.py` dispatches to command handlers (backup, restic passthrough, unmount, list)
- Configuration-driven: YAML sessions feed orchestrators that prepare destinations, mount/unmount resources, then call Restic/Rsync helpers
- Mount/finder layers encapsulate physical devices, rclone remotes, and gocryptfs wrappers to keep platform-specific logic contained
- No long-lived daemons; scheduling is delegated to OS services via scripts in `scripts/`

### Testing Strategy
- Pytest with coverage is configured; add unit tests for new behavior, especially around config parsing and mount orchestration (mock external commands)
- Favor fast, isolated tests; gate integration/e2e tests behind explicit flags because they require system binaries and devices/remotes
- Aim to keep coverage from regressing when adding features; use type checking as an additional safety net

### Git Workflow
- Git Flow: stable `main`, integration `dev`, feature branches off `dev`; merge via PRs
- Prefer small, reviewable changes; rebase to keep history linear before merging
- Versioning comes from Git tags (`hatch-vcs`); tag releases as `vX.Y.Z`

## Domain Context
Focus is on reliable, repeatable backups to heterogeneous destinations. Users describe sources and targets (local paths, labeled external drives, rclone remotes) plus optional encryption layers. The tool auto-mounts destinations, runs the chosen backup engine, and unmounts/cleans temporary mountpoints, minimizing risk of leaving devices attached or unencrypted.

## Important Constraints
- Keep runtime dependencies minimal; rely on external CLI tools already installed by the user
- Cross-platform behavior must avoid OS-specific assumptions; guard features that only work on certain platforms (e.g., masking with proot/rustic)
- Temporary directories and mounts must use restrictive permissions and be cleaned up on failure paths
- Avoid storing secrets outside user-provided configs/environment; prefer passing repo passwords via env vars/flags

## External Dependencies
- Restic (primary backup engine) and Rsync (alternative/supplemental)
- Rclone for remote targets (cloud/object storage)
- gocryptfs for optional encryption of mounted destinations
- proot (Android/Termux masking) and rustic (macOS masking) when users enable masking
