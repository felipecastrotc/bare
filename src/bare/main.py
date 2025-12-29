#!/usr/bin/python

from __future__ import annotations

import argparse
import collections.abc
import copy
import logging
import os
import shutil
import sys
import textwrap
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from . import DestinationHandler, MountManager, Restic, Rsync
from .utils import InfoOnlyFormatter, get_hostname

# Logger setup
handler = logging.StreamHandler()
handler.setFormatter(InfoOnlyFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

DEFAULT_SESSION_FILENAME = "session.yml"
DEFAULT_SESSION_ENV_VAR = "BARE_SESSION"
DEFAULT_SESSION_PATH = Path("~/.config/bare") / DEFAULT_SESSION_FILENAME

RESTIC_SHORTCUTS = {"snapshots": "snapshots", "stats": "stats", "check": "check"}


def update_nested(d: dict[str, Any] | None, u: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively update a nested dictionary `d` with values from dictionary `u`."""
    if d is None:
        return dict(u)
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_nested(d.get(k, {}), v)
        else:
            d[k] = v
    return d


default_var: dict[str, Any] = {
    "hostname": None,
    "source": [None],
    "mask": None,
    "restic": {
        "password": None,
        "args": {},
        "enable": True,
        "restic_folder": "restic",
        "runner": "restic",
        "bin_path": None,
        "forget": None,
        "skip-maintain": False,
    },
    "rsync": {
        "password": None,
        "args": {},
        "enable": False,
        "rsync_folder": "rsync",
    },
    "check_hostname": False,
}


def looks_like_rclone_remote(destination: str) -> bool:
    if destination.startswith("rest:"):
        return False
    if destination.startswith("~"):
        return False
    if os.path.isabs(destination):
        return False
    return ":" in destination


def is_executable_available(candidate: str | None) -> bool:
    if not candidate:
        return False
    path = Path(candidate).expanduser()
    if path.exists() and os.access(path, os.X_OK):
        return True
    return shutil.which(candidate) is not None


def collect_missing_dependencies(configs: Mapping[str, Mapping[str, Any]]) -> list[str]:
    missing: set[str] = set()
    for config in configs.values():
        restic_cfg = config.get("restic", {})
        if restic_cfg.get("enable"):
            runner = restic_cfg.get("runner", "restic")
            restic_bin = restic_cfg.get("bin_path") or runner
            if not is_executable_available(restic_bin):
                missing.add(restic_bin)

        rsync_cfg = config.get("rsync", {})
        if rsync_cfg.get("enable") and not is_executable_available("rsync"):
            missing.add("rsync")

        if looks_like_rclone_remote(
            config.get("destination", "")
        ) and not is_executable_available("rclone"):
            missing.add("rclone")
    return sorted(missing)


def resolve_session_path(
    session_arg: str | None, env: Mapping[str, str] | None = None
) -> Path:
    env = env or os.environ
    env_session = env.get(DEFAULT_SESSION_ENV_VAR)
    candidates: list[Path] = []

    if session_arg:
        candidates.append(Path(session_arg).expanduser())
    elif env_session:
        candidates.append(Path(env_session).expanduser())
    else:
        candidates.append(Path(DEFAULT_SESSION_FILENAME))
        candidates.append(DEFAULT_SESSION_PATH.expanduser())

    for path in candidates:
        if path.exists():
            resolved = path.resolve()
            logger.info(f"Using session file: {resolved}")
            return resolved

    raise FileNotFoundError(
        f"Session file not found. Looked for: {', '.join(str(p.resolve()) for p in candidates)}. "
        f"Create one or pass a path with --session or set {DEFAULT_SESSION_ENV_VAR}."
    )


def load_session(session_path: Path) -> dict[str, Any]:
    try:
        with session_path.open() as f:
            session = yaml.safe_load(f) or {}
    except FileNotFoundError:
        raise
    except yaml.YAMLError as exc:
        raise ValueError(f"Failed to parse session file {session_path}: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Unable to read session file {session_path}: {exc}") from exc

    if not isinstance(session, dict):
        raise ValueError(
            f"Session file {session_path} must contain a mapping of targets"
        )
    return session


def normalize_config(config: Mapping[str, Any]) -> dict[str, Any]:
    merged = update_nested(copy.deepcopy(default_var), config)
    if not merged.get("hostname"):
        merged["hostname"] = get_hostname()

    sources = merged.get("source", [])
    if isinstance(sources, str) or not isinstance(sources, list):
        merged["source"] = [sources]

    return merged


def build_cli_config(args: argparse.Namespace, command: str) -> dict[str, Any] | None:
    destination = getattr(args, "destination", None)
    if not destination:
        return None

    source = getattr(args, "source", None)
    restic_password = getattr(args, "restic_password", None)
    hostname = getattr(args, "hostname", None) or get_hostname()

    cli_config: dict[str, Any] = {
        "hostname": hostname,
        "destination": destination,
    }
    if source:
        cli_config["source"] = [source] if isinstance(source, str) else source
    if restic_password:
        cli_config.setdefault("restic", {})["password"] = restic_password

    return cli_config


def build_configs(
    session: Mapping[str, Any],
    cli_config: dict[str, Any] | None,
    target: str | None,
) -> dict[str, dict[str, Any]]:
    configs: dict[str, dict[str, Any]] = {}
    for name, config in session.items():
        if not isinstance(config, Mapping):
            continue
        configs[name] = normalize_config(config)

    if cli_config:
        configs["cmdline"] = normalize_config(cli_config)

    if target:
        configs = {k: v for k, v in configs.items() if k == target}

    configs = {k: v for k, v in configs.items() if v.get("destination")}
    return configs


def summarize_backup_plan(configs: Mapping[str, Mapping[str, Any]]) -> list[str]:
    lines = []
    for name, cfg in configs.items():
        engines: list[str] = []
        if cfg.get("restic", {}).get("enable"):
            engines.append("restic")
        if cfg.get("rsync", {}).get("enable"):
            engines.append("rsync")
        destination = cfg.get("destination", "")
        lines.append(
            f"- {name}: destination={destination} engines={','.join(engines) or 'none'}"
        )
    return lines


def prompt_confirmation(message: str) -> bool:
    reply = input(f"{message} [y/N]: ").strip().lower()  # noqa: S322
    return reply in ("y", "yes")


def build_parser() -> argparse.ArgumentParser:
    examples = textwrap.dedent(
        """
        Examples:
          bare backup --session ~/.config/bare/session.yml
          bare backup --session ~/.config/bare/session.yml --target home --yes
          bare snapshots --session ~/.config/bare/session.yml
          bare restic --session ~/.config/bare/session.yml snapshots --tag weekly
        """
    )
    parser = argparse.ArgumentParser(
        description="BARE: Backup Automation with Replication and Encryption",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=examples,
    )
    subparser = parser.add_subparsers(help="Commands", dest="command")

    # Backup subparser
    backupparser = subparser.add_parser(
        "backup",
        help="Run backups for configured targets using the session file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Perform backup using session configuration with optional confirmation and dry-run.",
    )
    backupparser.add_argument(
        "--hostname",
        default=None,
        help="Override hostname for this run (default: current hostname).",
    )
    backupparser.add_argument(
        "--destination",
        default=None,
        help="Destination label/path/rclone remote for CLI-only runs.",
    )
    backupparser.add_argument(
        "--source",
        default=None,
        help="Source path for CLI-only runs (session.yml normally controls this).",
    )
    backupparser.add_argument(
        "--restic-password",
        default=None,
        help="Restic password override for CLI-only runs.",
    )
    backupparser.add_argument(
        "--session",
        default=None,
        help=f"Session file path (default: {DEFAULT_SESSION_PATH}).",
    )
    backupparser.add_argument(
        "--target",
        default=None,
        help="Run only the named target from the session file.",
    )
    backupparser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt and proceed automatically.",
    )
    backupparser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned mounts and commands without invoking restic or rsync.",
    )

    # Restic subparser
    resticparser = subparser.add_parser(
        "restic",
        help="Run a restic command against configured targets with shortcuts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Execute restic commands without managing mounts; includes shortcuts for common operations.",
    )
    resticparser.add_argument(
        "--session",
        default=None,
        help=f"Session file path (default: {DEFAULT_SESSION_PATH}).",
    )
    resticparser.add_argument(
        "--target",
        default=None,
        help="Run only the named target from the session file.",
    )
    resticparser.add_argument(
        "--snapshots",
        action="store_true",
        help="Shortcut: run `restic snapshots` for each target.",
    )
    resticparser.add_argument(
        "--stats",
        action="store_true",
        help="Shortcut: run `restic stats` for each target.",
    )
    resticparser.add_argument(
        "--check",
        action="store_true",
        help="Shortcut: run `restic check` for each target.",
    )
    resticparser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show commands without invoking restic.",
    )
    resticparser.add_argument(
        "restic_args",
        nargs=argparse.REMAINDER,
        help="Restic command to run (e.g., snapshots --tag weekly).",
    )

    # Snapshots alias
    snapshotparser = subparser.add_parser(
        "snapshots",
        help="Alias for `restic --snapshots`.",
        description="Quickly list restic snapshots for all configured targets.",
    )
    snapshotparser.add_argument(
        "--session",
        default=None,
        help=f"Session file path (default: {DEFAULT_SESSION_PATH}).",
    )
    snapshotparser.add_argument(
        "--target",
        default=None,
        help="Run only the named target from the session file.",
    )
    snapshotparser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show commands without invoking restic.",
    )
    snapshotparser.add_argument(
        "restic_args",
        nargs=argparse.REMAINDER,
        help="Additional restic arguments to pass to snapshots.",
    )

    # Umount parser
    umountparser = subparser.add_parser(
        "umount",
        help="Unmount and clean temporary folders created by BARE.",
    )
    umountparser.add_argument(
        "--target",
        default=None,
        help="Optional target filter (reserved for future use).",
    )

    # List parser
    listparser = subparser.add_parser(
        "list",
        help="List the sessions and configurations from the session file.",
    )
    listparser.add_argument(
        "--session",
        default=None,
        help=f"Session file path (default: {DEFAULT_SESSION_PATH}).",
    )

    # Maintain parser
    maintainparser = subparser.add_parser(
        "maintain",
        help="Run maintenance (forget/check) defined in the session file.",
    )
    maintainparser.add_argument(
        "--session",
        default=None,
        help=f"Session file path (default: {DEFAULT_SESSION_PATH}).",
    )
    maintainparser.add_argument(
        "--target",
        default=None,
        help="Run only the named target from the session file.",
    )

    return parser


def get_restic_instance(
    config: dict[str, Any],
    destination_path: str,
    name: str,
    destination_type: str | None = None,
) -> Restic:
    restic_folder = (
        ""
        if destination_type == "restic_rest_server"
        else config["restic"]["restic_folder"]
    )
    return Restic(
        destination_path,
        config["restic"]["password"],
        restic_folder=restic_folder,
        hostname=config["hostname"],
        name=name,
        check_hostname=config["check_hostname"],
        runner=config["restic"]["runner"],
        bin_path=config["restic"]["bin_path"],
    )


def get_rsync_instance(
    config: dict[str, Any], destination_path: str, name: str
) -> Rsync:
    return Rsync(
        destination_path,
        rsync_folder=config["rsync"]["rsync_folder"],
        hostname=config["hostname"],
        name=name,
        check_hostname=config["check_hostname"],
    )


def post_backup_restic(
    restic_instance: Restic, config: dict[str, Any], dry_run: bool
) -> None:
    if dry_run:
        logger.info("Would run restic forget/check maintenance.")
        return
    if not config["restic"]["skip-maintain"]:
        forget_config = config.get("restic", {}).get("forget")
        if isinstance(forget_config, dict):
            logger.info("Restic: Pruning old snapshots...")
            restic_instance.forget(forget_config)
            logger.info("Restic: Finished pruning old snapshots!")

        check_config = config.get("restic", {}).get("check")
        if isinstance(check_config, dict):
            logger.info("Restic: Checking repository...")
            restic_instance.check(check_config)
            logger.info("Restic: Finished checking repository!")


def backup(configs: dict[str, dict[str, Any]], dry_run: bool, assume_yes: bool) -> None:
    if not configs:
        logger.info("No backup targets found in the session file.")
        return

    logger.info("Backup plan:")
    for line in summarize_backup_plan(configs):
        logger.info(line)

    if dry_run:
        logger.info("Dry-run enabled. No mounts or backup commands will be executed.")

    if (
        not dry_run
        and not assume_yes
        and not prompt_confirmation("Proceed with backup?")
    ):
        logger.info("Aborted by user.")
        return

    for name, config in configs.items():
        destination = config["destination"]
        handler = DestinationHandler(destination)
        if dry_run:
            logger.info(
                f"[dry-run] {name}: would mount '{destination}' (type={handler.destination_type}) "
                f"and run {('restic ' if config['restic']['enable'] else '')}"
                f"{('rsync' if config['rsync']['enable'] else '')}"
            )
            continue

        logger.info(f"Starting backup for {name} to {destination}")
        try:
            with handler as destination_path:
                if config["restic"]["enable"]:
                    logger.info("Starting restic backup...")
                    restic_instance = get_restic_instance(
                        config, destination_path, name, handler.destination_type
                    )
                    mask = config["mask"]
                    args = config["restic"]["args"]
                    for i, source in enumerate(config["source"]):
                        if source is None:
                            logger.info("Skipping empty source entry.")
                            continue
                        mask_i = mask[i] if isinstance(mask, list) else mask
                        restic_instance.backup(source, args, mask_i)
                    logger.info("Restic backup done!")
                    post_backup_restic(restic_instance, config, dry_run=False)
                if (
                    config["rsync"]["enable"]
                    and handler.destination_type != "restic_rest_server"
                ):
                    logger.info("Starting rsync backup...")
                    rsync = get_rsync_instance(config, destination_path, name)
                    mask = config["mask"]
                    args = config["rsync"]["args"]
                    for i, source in enumerate(config["source"]):
                        if source is None:
                            logger.info("Skipping empty source entry.")
                            continue
                        mask_i = mask[i] if isinstance(mask, list) else mask
                        rsync.backup(source, args, mask_i)
                    logger.info("Rsync backup done!")
                elif config["rsync"]["enable"]:
                    logger.info(
                        "The destination is a Restic rest server; skipping rsync."
                    )
        except AssertionError as e:
            logger.info(f"Error during backup: {e}")
            if "Unable to find" in str(e) and len(configs) > 1:
                logger.info("Skipping to the next drive.")


def run_restic_command(
    configs: dict[str, dict[str, Any]],
    command: str,
    dry_run: bool,
) -> None:
    if not configs:
        logger.info("No restic targets found in the session file.")
        return
    if not command:
        logger.info(
            "No restic command provided. Use --snapshots, --stats, --check, or pass a command."
        )
        return

    if dry_run:
        logger.info("Dry-run enabled. Commands will be shown but not executed.")

    for name, config in configs.items():
        destination = config["destination"]
        handler = DestinationHandler(destination)

        if dry_run:
            logger.info(
                f"[dry-run] {name}: would mount '{destination}' (type={handler.destination_type}) "
                f"and run restic command: {command}"
            )
            continue

        try:
            with handler as destination_path:
                restic_instance = get_restic_instance(
                    config, destination_path, name, handler.destination_type
                )
                _ = restic_instance.run(command)
        except AssertionError as e:
            logger.info(f"Error during Restic command: {e}")
            if "Unable to find" in str(e) and len(configs) > 1:
                logger.info("Skipping to the next drive.")


def maintain(configs: dict[str, dict[str, Any]]) -> None:
    if not configs:
        logger.info("No maintenance targets found in the session file.")
        return

    for name, config in configs.items():
        logger.info(f"Starting maintenance for {name} to {config['destination']}")
        try:
            handler = DestinationHandler(config["destination"])
            with handler as destination_path:
                if config["restic"]["enable"]:
                    logger.info("Maintaining restic...")
                    restic_instance = get_restic_instance(
                        config, destination_path, name, handler.destination_type
                    )
                    post_backup_restic(restic_instance, config, dry_run=False)
                    logger.info("Restic maintenance done!")
                if (
                    config["rsync"]["enable"]
                    and handler.destination_type != "restic_rest_server"
                ):
                    logger.info("NOT IMPLEMENTED YET!")
                elif config["rsync"]["enable"]:
                    logger.info("The destination is a Restic rest server")
        except AssertionError as e:
            logger.info(f"Error during maintenance: {e}")


def umount() -> None:
    try:
        mount_mgmt = MountManager()
        mount_mgmt.umount_all()
        mount_mgmt.clean()
    except AssertionError as e:
        logger.info(f"Error during unmount: {e}")


def list_func(configs: dict[str, dict[str, Any]]) -> None:
    if not configs:
        logger.info("No targets found in the session file.")
        return
    logger.info(yaml.dump(list(configs.keys())))


def build_restic_command_from_args(args: argparse.Namespace) -> str:
    restic_args: Iterable[str] = getattr(args, "restic_args", []) or []
    if args.command == "snapshots" or getattr(args, "snapshots", False):
        base = RESTIC_SHORTCUTS["snapshots"]
        suffix = " ".join(restic_args).strip()
        return f"{base} {suffix}".strip()
    if getattr(args, "stats", False):
        base = RESTIC_SHORTCUTS["stats"]
        suffix = " ".join(restic_args).strip()
        return f"{base} {suffix}".strip()
    if getattr(args, "check", False):
        base = RESTIC_SHORTCUTS["check"]
        suffix = " ".join(restic_args).strip()
        return f"{base} {suffix}".strip()
    if restic_args:
        return " ".join(restic_args).strip()
    return ""


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "umount":
        umount()
        return

    session_required = args.command in {
        "backup",
        "restic",
        "snapshots",
        "list",
        "maintain",
    }
    session_data: dict[str, Any] = {}

    if session_required:
        try:
            session_path = resolve_session_path(getattr(args, "session", None))
            session_data = load_session(session_path)
        except (FileNotFoundError, ValueError, OSError) as exc:
            logger.error(exc)
            sys.exit(1)

    cli_config = (
        build_cli_config(args, args.command) if args.command == "backup" else None
    )
    target = getattr(args, "target", None)
    configs = build_configs(session_data, cli_config, target)

    if args.command in {"backup", "restic", "snapshots"}:
        missing = collect_missing_dependencies(configs)
        if missing:
            logger.error(
                "Missing required dependencies: %s. Please install them or adjust your configuration.",
                ", ".join(missing),
            )
            sys.exit(1)

    if args.command == "backup":
        backup(configs, dry_run=args.dry_run, assume_yes=args.yes)
    elif args.command in {"restic", "snapshots"}:
        restic_cmd = build_restic_command_from_args(args)
        run_restic_command(configs, restic_cmd, dry_run=args.dry_run)
    elif args.command == "list":
        list_func(configs)
    elif args.command == "maintain":
        maintain(configs)


if __name__ == "__main__":
    main()
