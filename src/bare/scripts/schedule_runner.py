#!/usr/bin/env python3
"""
Backup launcher for bare backup (custom CLI) inside micromamba environment.
Handles daily execution, logging, Tailscale startup, and connectivity checks.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
import platform
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from shutil import which

IS_DRY_RUN = "--dry-run" in sys.argv
BACKUP_SERVER_HOST = "restic.local"
BACKUP_SERVER_PORT = "80"


@dataclass
class Config:
    """Configuration for the backup script."""

    bare_bin: Path
    log_file: Path
    state_file: Path
    server_host: str
    server_port: int
    tailscale_bin: Path


def setup_logging(log_file: Path):
    """Initializes logging to both file and stdout.

    Args:
        log_file: Path to the log file.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def today_str():
    """Returns today's date in ISO format.

    Returns:
        A string representing today's date (YYYY-MM-DD).
    """
    return dt.date.today().isoformat()


def already_done_today(state_file: Path) -> bool:
    """Checks whether the backup was successfully run today.

    Args:
        state_file: Path to the file storing the last successful run info.

    Returns:
        True if the backup has already run successfully today; otherwise False.
    """
    if not state_file.exists():
        return False
    try:
        return state_file.read_text().strip().endswith(f"{today_str()} SUCCESS")
    except Exception:
        return False


def mark_run_result(state_file: Path, result: str):
    """Marks the result of the backup operation in the state file.

    Args:
        state_file: Path to the state file.
        result: A result string, e.g., "SUCCESS" or "FAILURE".
    """
    state_file.write_text(f"{today_str()} {result}")


def check_port(host: str, port: int, timeout: float = 3.0) -> bool:
    """Checks if a TCP port on a host is reachable.

    Args:
        host: Hostname or IP address.
        port: TCP port number.
        timeout: Timeout in seconds.

    Returns:
        True if the port is reachable; otherwise False.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def run_command(cmd: list, description: str = ""):
    """Runs a shell command, optionally logging its description.

    Args:
        cmd: List of command arguments.
        description: Optional description for logging.

    Returns:
        subprocess.CompletedProcess instance with execution results.
    """
    logging.info(f"Running: {description or ' '.join(cmd)}")
    if IS_DRY_RUN:
        logging.info("[Dry-run] Skipping execution.")
        return subprocess.CompletedProcess(cmd, returncode=0)
    cp = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if cp.returncode != 0:
        logging.error(
            "Backup failed (exit=%d).\n--- STDOUT ---\n%s\n--- STDERR ---\n%s",
            cp.returncode,
            cp.stdout,
            cp.stderr,
        )
    if cp.stdout:
        logging.info(cp.stdout)
    if cp.stderr:
        logging.warning(cp.stderr)
    return cp


def is_tailscale_running(tailscale_bin: Path) -> bool:
    """Checks whether the Tailscale daemon is currently running.

    Args:
        tailscale_bin: Path to the Tailscale binary.

    Returns:
        True if Tailscale is running; otherwise False.
    """
    try:
        cp = subprocess.run(
            [tailscale_bin, "status"],
            capture_output=True,
            text=True,
        )
        return "100." in cp.stdout and cp.returncode == 0
    except Exception:
        return False


def ensure_tailscale(cfg: Config) -> bool:
    """Ensures Tailscale is running if the backup server is unreachable.

    Args:
        cfg: Config object with Tailscale and server settings.

    Returns:
        True if Tailscale was started; False otherwise.
    """
    if not cfg.tailscale_bin.exists():
        logging.warning("Tailscale not found. Continuing without it.")
        return False

    if check_port(cfg.server_host, cfg.server_port):
        return False

    if not is_tailscale_running(cfg.tailscale_bin):
        logging.info("Starting Tailscale...")
        try:
            run_command([str(cfg.tailscale_bin), "up"], description="Tailscale up")
            return True
        except Exception:
            logging.error("Failed to start Tailscale.")
            return False
    return False


def shutdown_tailscale(cfg: Config):
    """Attempts to shut down the Tailscale connection.

    Args:
        cfg: Config object containing the Tailscale binary path.
    """
    try:
        logging.info("Stopping Tailscale...")
        run_command([str(cfg.tailscale_bin), "down"], description="Tailscale down")
    except Exception as ex:
        logging.error(f"Failed to stop Tailscale: {ex}")


def perform_backup(cfg: Config):
    """Runs the bare backup command. It assumes that bare is installed."""
    cmd = [cfg.bare_bin, "backup"]
    run_command(cmd, description="bare backup")


def load_config() -> Config:
    """Loads configuration from environment variables and sets defaults.

    Returns:
        Config object populated with paths, host info, and environment names.
    """
    home = Path.home()

    if platform.system() == "Darwin":
        log_dir = home / "Library" / "Logs"
    else:
        log_dir = home / ".local" / "share" / "logs"

    state_file = home / ".local" / "state" / "bare" / "last_success.txt"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    return Config(
        bare_bin=Path(
            os.environ.get(
                "BARE_BIN",
                which("bare") or "/opt/bare/bare",
            )
        ),
        log_file=log_dir / "bare.log",
        state_file=state_file,
        server_host=os.environ.get("BACKUP_SERVER_HOST", BACKUP_SERVER_HOST),
        server_port=int(os.environ.get("BACKUP_SERVER_PORT", BACKUP_SERVER_PORT)),
        tailscale_bin=Path(
            os.environ.get(
                "TAILSCALE_BIN", which("tailscale") or "/opt/homebrew/bin/tailscale"
            )
        ),
    )


def main():
    """Main entry point for the backup script.

    Performs:
        - Configuration loading
        - Logging setup
        - Backup execution (if not already done today)
        - Tailscale management
        - Success/failure state recording

    Returns:
        0 if successful, 1 if an error occurred.
    """
    cfg = load_config()
    setup_logging(cfg.log_file)

    if already_done_today(cfg.state_file):
        logging.info(f"Backup already completed today ({today_str()}). Exiting.")
        return 0

    tailscale_started = ensure_tailscale(cfg)

    if not check_port(cfg.server_host, cfg.server_port):
        logging.error(f"Server {cfg.server_host}:{cfg.server_port} is unreachable.")
        if tailscale_started:
            shutdown_tailscale(cfg)
        return 1

    try:
        perform_backup(cfg)
        mark_run_result(cfg.state_file, "SUCCESS")
        logging.info("Backup completed successfully.")
    except Exception as e:
        mark_run_result(cfg.state_file, "FAILURE")
        logging.error(f"Backup failed: {e}")
        return 1
    finally:
        if tailscale_started:
            shutdown_tailscale(cfg)

    return 0


if __name__ == "__main__":
    sys.exit(main())
