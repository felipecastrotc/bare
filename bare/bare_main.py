#!/usr/bin/python

import os
import yaml
import argparse
import copy
import collections.abc
from bare import Restic, Rsync, DestinationHandler
from bare import MountManager
from .utils import get_hostname

# from utils import get_hostname, Backup, Restic, Mount, DestinationHandler


def update_nested(d, u):
    """
    Recursively update a nested dictionary `d` with values from dictionary `u`.
    This is useful for merging configurations.
    """
    if d is None:
        return u
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_nested(d.get(k, {}), v)
        else:
            d[k] = v
    return d


default_var = {
    "hostname": None,
    "source": [None],
    "mask": None,
    "restic": {
        "password": None,
        "args": {},
        "enable": True,
        "restic_folder": "restic",
        "runner": "restic",
        "enable": True,
        "forget": None,
    },
    "rsync": {
        "password": None,
        "args": {},
        "enable": False,
        "rsync_folder": "rsync",
    },
    "check_hostname": False,
}


def get_restic_instance(config, destination_path, name, destination_type=None):
    if destination_type == "restic_rest_server":
        restic_folder = ""
    else:
        restic_folder = config["restic"]["restic_folder"]
    restic_instance = Restic(
        destination_path,
        config["restic"]["password"],
        restic_folder=restic_folder,
        hostname=config["hostname"],
        name=name,
        check_hostname=config["check_hostname"],
        runner=config["restic"]["runner"],
    )
    print(config)
    return restic_instance


def get_rsync_instance(config, destination_path, name):
    rsync_instance = Rsync(
        destination_path,
        rsync_folder=config["rsync"]["rsync_folder"],
        hostname=config["hostname"],
        name=name,
        check_hostname=config["check_hostname"],
    )
    return rsync_instance


def post_backup_restic(restic_instance, config):
    if isinstance(config["restic"]["forget"], dict):
        print("Restic: Prunning old snapshots...")
        restic_instance.forget(config["restic"]["forget"])
        print("Restic: Finished prunning old snapshots!")


def backup(var):
    """
    Perform backup operations using the provided configuration. It handles both
    Restic and Rsync backups based on the configuration.
    """
    for name, config in var.items():
        print(f"Starting backup for {name} to {config['destination']}")
        try:
            dh = DestinationHandler(config["destination"])
            with dh as destination_path:
                if config["restic"]["enable"]:
                    print("Starting restic backup!")
                    restic_instance = get_restic_instance(
                        config, destination_path, name, dh.destination_type
                    )
                    mask = config["mask"]
                    args = config["restic"]["args"]
                    for i, source in enumerate(config["source"]):
                        mask_i = mask[i] if isinstance(mask, list) else mask
                        restic_instance.backup(source, args, mask_i)
                    print("Restic backup done!")
                    post_backup_restic(restic_instance, config)
                if (
                    config["rsync"]["enable"]
                    and dh.destination_type != "restic_rest_server"
                ):
                    print("Starting rsync backup!")
                    rsync = get_rsync_instance(config, destination_path, name)
                    mask = config["mask"]
                    args = config["rsync"]["args"]
                    for i, source in enumerate(config["source"]):
                        mask_i = mask[i] if isinstance(mask, list) else mask
                        rsync.backup(source, args, mask_i)
                    print("Rsync backup done!")
                elif config["rsync"]["enable"]:
                    print("The destination is a Restic rest server")
        except AssertionError as e:
            print(f"Error during backup: {e}")
            if "Unable to find" in str(e):
                if len(var) > 1:
                    print("Skipping to the next drive.")


def restic(var, unknown):
    """
    Execute a Restic command for each configuration entry.
    """
    for name, config in var.items():
        try:
            dh = DestinationHandler(config["destination"])
            with dh as destination_path:
                restic_instance = get_restic_instance(
                    config, destination_path, name, dh.destination_type
                )
                _ = restic_instance.run(" ".join(unknown))
        except AssertionError as e:
            print(f"Error during Restic command: {e}")
            if "Unable to find" in str(e):
                if len(var) > 1:
                    print("Skipping to the next drive.")


def umount(var):
    """
    Unmount and clean the temporary folders created during the backup.
    """
    try:
        mount_mgmt = MountManager()
        mount_mgmt.umount_all()
        mount_mgmt.clean()
    except AssertionError as e:
        print(f"Error during unmount: {e}")


def list_func(var, unknown):
    """
    List all available sessions and configurations.
    """
    print(yaml.dump(list(var.keys())))


def router(cmd, var, unknown, target):
    """
    Main function to route commands to the appropriate function.
    """
    if cmd == "list":
        list_func(var, unknown)
    else:
        if target:
            var = {k: v for k, v in var.items() if k == target}

        if cmd == "backup":
            backup(var)
        elif cmd == "restic":
            restic(var, unknown)
        elif cmd == "umount":
            umount(var)


def main():
    # Initialize parser
    #
    parser = argparse.ArgumentParser(
        description="BARE: Backup Automation with Replication and Encryption"
    )
    subparser = parser.add_subparsers(help="Sub-command help", dest="command")

    # Backup subparser
    backupparser = subparser.add_parser(
        "backup",
        help="Commands for backup functionality. Configuration in session.yml overwrites the passed arguments.",
    )
    backupparser.add_argument(
        "--hostname",
        default=get_hostname(),
        nargs="?",
        help="Computer name to be the backup parent folder, default is the current computer name.",
    )
    backupparser.add_argument(
        "--destination",
        default="",
        nargs="?",
        help="The device destination where the backup will be stored.",
    )
    backupparser.add_argument(
        "--source",
        default=os.path.expanduser("~"),
        nargs="?",
        help="The folder to be backed up, default is the user folder.",
    )
    backupparser.add_argument(
        "--restic-password",
        default="",
        nargs="?",
        help="The password for Restic. Can be omitted if configured in the YAML file.",
    )
    backupparser.add_argument(
        "--session",
        default="session.yml",
        nargs="?",
        help="Custom session file to be used.",
    )
    backupparser.add_argument(
        "--target",
        default=None,
        nargs="?",
        help="The backup setting to be used. Use 'list' to view available options.",
    )

    # Restic subparser
    resticparser = subparser.add_parser(
        "restic",
        help="Helper to use Restic without mounting it or dealing with the repository directory.",
    )
    resticparser.add_argument(
        "--hostname",
        default=get_hostname(),
        nargs="?",
        help="Computer name to be the backup parent folder, default is the current computer name.",
    )
    resticparser.add_argument(
        "--restic-password",
        default="",
        nargs="?",
        help="The password for Restic. Can be omitted if configured in the YAML file.",
    )
    resticparser.add_argument(
        "--destination",
        default="",
        nargs="?",
        help="The device where the backup will be stored.",
    )
    resticparser.add_argument(
        "--session",
        default="session.yml",
        nargs="?",
        help="Custom session file to be used.",
    )
    resticparser.add_argument(
        "--target",
        default=None,
        nargs="?",
        help="The backup setting to be used. Use 'list' to view available options.",
    )

    # Umount parser
    umountparser = subparser.add_parser(
        "umount",
        help="Unmount and clean the temporary folders created.",
    )
    umountparser.add_argument(
        "--hostname",
        default=get_hostname(),
        nargs="?",
        help="Computer name to be the backup parent folder, default is the current computer name.",
    )
    umountparser.add_argument(
        "--destination",
        default="",
        nargs="?",
        help="The device destination where the backup will be stored.",
    )
    umountparser.add_argument(
        "--target",
        default=None,
        nargs="?",
        help="The backup setting to be used. Use 'list' to view available options.",
    )

    # List parser
    listparser = subparser.add_parser(
        "list",
        help="List the sessions and configurations.",
    )

    # Get arguments
    args, unknown = parser.parse_known_args()
    var = vars(args)

    target = var.get("target")

    # Load the session configuration
    default_session = "session.yml"
    default_home = os.path.expanduser(f"~/.config/bare/{default_session}")

    session_file = var.get("session", default_session)
    session_home = os.path.expanduser(f"~/.config/bare/{session_file}")

    if os.path.exists(session_file):
        with open(session_file) as f:
            session = yaml.load(f, Loader=yaml.FullLoader)
    elif os.path.exists(session_home):
        with open(session_home) as f:
            session = yaml.load(f, Loader=yaml.FullLoader)
    else:
        session = {}

    # Combine command-line arguments and session configuration
    cmd = var.pop("command")
    var = {"cmdline": var}
    var.update(session)

    # Clean and validate configuration
    var = {k: v for k, v in var.items() if v and v.get("destination")}
    var = {k: update_nested(copy.deepcopy(default_var), v) for k, v in var.items()}

    if var:
        router(cmd, var, unknown, target)


if __name__ == "__main__":
    main()
