from __future__ import annotations

import argparse
import json
import os
import stat
from pathlib import Path

import pytest

from bare import main as cli_main
from bare.bare.restic import Restic
from bare.bare.rsync import Rsync
from bare.destination_handler import DestinationHandler
from bare.finder.devices import DeviceFinder
from bare.finder.physical import DriveFinderDarwin, DriveFinderLinux
from bare.finder.rclone import RcloneFinder
from bare.mount_manager import MountManager, MountPointFinder
from bare.utils import dict2args, modify_command_for_os

# ---------- main.py helpers ----------


def test_update_nested_merges_recursively() -> None:
    base = {"a": {"b": 1}, "c": 2}
    updates = {"a": {"d": 3}, "c": 4}

    merged = cli_main.update_nested(base, updates)

    assert merged["a"] == {"b": 1, "d": 3}
    assert merged["c"] == 4


@pytest.mark.parametrize(
    "dest,expected",
    [
        ("remote:bucket", True),
        ("rest:https://example.com", False),
        ("/abs/path", False),
        ("~/relative", False),
    ],
)
def test_looks_like_rclone_remote(dest: str, expected: bool) -> None:
    assert cli_main.looks_like_rclone_remote(dest) is expected


def test_is_executable_available_with_tempfile(tmp_path: Path) -> None:
    executable = tmp_path / "tool"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(executable.stat().st_mode | stat.S_IEXEC)

    assert cli_main.is_executable_available(str(executable)) is True
    assert cli_main.is_executable_available(str(executable.parent / "missing")) is False


def test_collect_missing_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli_main,
        "is_executable_available",
        lambda name: name not in {"restic", "rclone", "rsync"},
    )
    configs = {
        "target": {
            "destination": "remote:bucket",
            "restic": {"enable": True, "runner": "restic"},
            "rsync": {"enable": True},
        }
    }

    missing = cli_main.collect_missing_dependencies(configs)

    assert missing == sorted(["restic", "rclone", "rsync"])


def test_normalize_and_build_configs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_main, "get_hostname", lambda: "host")
    session = {
        "one": {
            "destination": "/tmp/dest",
            "restic": {"password": "pw"},
            "source": "src",
        }
    }
    cli_cfg = {"destination": "/tmp/cli", "restic": {"password": "pw2"}}

    configs = cli_main.build_configs(session, cli_cfg, target=None)

    assert "one" in configs and "cmdline" in configs
    assert configs["one"]["hostname"] == "host"
    assert configs["one"]["source"] == ["src"]
    assert configs["cmdline"]["restic"]["password"] == "pw2"


def test_build_cli_config_builds_when_destination_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_main, "get_hostname", lambda: "local")
    args = argparse.Namespace(
        destination="/tmp/d", source="s", restic_password="pw", hostname=None
    )

    cfg = cli_main.build_cli_config(args, "backup")

    assert cfg["destination"] == "/tmp/d"
    assert cfg["source"] == ["s"]
    assert cfg["restic"]["password"] == "pw"
    assert cfg["hostname"] == "local"


def test_build_restic_command_from_args_shortcuts() -> None:
    args = argparse.Namespace(
        command="snapshots",
        snapshots=True,
        stats=False,
        check=False,
        restic_args=["--tag", "weekly"],
    )
    assert cli_main.build_restic_command_from_args(args) == "snapshots --tag weekly"

    args2 = argparse.Namespace(
        command="restic",
        snapshots=False,
        stats=True,
        check=False,
        restic_args=["--tag", "w"],
    )
    assert cli_main.build_restic_command_from_args(args2) == "stats --tag w"

    args3 = argparse.Namespace(
        command="restic",
        snapshots=False,
        stats=False,
        check=False,
        restic_args=["cat", "config"],
    )
    assert cli_main.build_restic_command_from_args(args3) == "cat config"


def test_build_configs_filters_target(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_main, "get_hostname", lambda: "host")
    session = {"one": {"destination": "/tmp/d", "restic": {"password": "pw"}}}
    configs = cli_main.build_configs(session, None, target="one")
    assert list(configs) == ["one"]


def test_list_func_logs_targets(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO")
    cli_main.list_func({"a": {}, "b": {}})
    assert "a" in caplog.text
    assert "b" in caplog.text


def test_prompt_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt: "y")  # noqa: ARG005
    assert cli_main.prompt_confirmation("ok") is True


# ---------- Mount manager and finders ----------


def test_mount_point_finder_linux(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    sample = "/dev/sda1 /mnt/tmp ext4 rw 0 0\n"
    fake_proc = tmp_path / "mounts"
    fake_proc.write_text(sample)

    import builtins

    real_open = builtins.open
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("builtins.open", lambda *_: real_open(fake_proc, "r"))

    finder = MountPointFinder()
    assert finder.find_device("/mnt/tmp") == "sda1"


def test_mount_point_finder_darwin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr(
        "bare.mount_manager.execute_command",
        lambda cmd: "/dev/disk1s1 on /Volumes/tmp\n",  # noqa: ARG005
    )
    finder = MountPointFinder()
    assert finder.find_device("/Volumes/tmp") == "disk1s1"


def test_mount_point_finder_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("platform.system", lambda: "Windows")
    monkeypatch.setattr(
        "bare.mount_manager.execute_command",
        lambda cmd: "VolumeName  DeviceID\nC:\n",  # noqa: ARG005
    )
    finder = MountPointFinder()
    assert finder.find_device("C:") == "C:"


def test_mount_manager_get_mounted_devices(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    temp_dir = tmp_path
    mount_dir = temp_dir / "BUP.tmp.one"
    mount_dir.mkdir()
    monkeypatch.setattr("bare.mount_manager.os.path.ismount", lambda path: True)
    monkeypatch.setattr("bare.mount_manager.os.listdir", lambda _: ["BUP.tmp.one"])

    mgr = MountManager()
    monkeypatch.setattr(mgr.mount_base, "get_dirname", lambda: str(temp_dir))
    monkeypatch.setattr(
        mgr.mount_finder,
        "find_device",
        lambda path: "sda1",  # noqa: ARG005
    )

    assert mgr.get_mounted_devices() == {
        "sda1": os.path.join(str(temp_dir), "BUP.tmp.one")
    }


def test_mount_manager_clean(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    temp_dir = tmp_path
    folder = temp_dir / "BUP.tmp.two"
    folder.mkdir()
    monkeypatch.setattr(
        "bare.mount_manager.os.listdir",
        lambda path: ["BUP.tmp.two"] if str(path) == str(temp_dir) else [],
    )
    monkeypatch.setattr("bare.mount_manager.os.path.ismount", lambda path: False)
    monkeypatch.setattr("bare.mount_manager.os.path.islink", lambda path: False)

    mgr = MountManager()
    monkeypatch.setattr(mgr.mount_base, "get_dirname", lambda: str(temp_dir))
    monkeypatch.setattr(mgr, "get_folders_created", lambda: ["BUP.tmp.two"])

    mgr.clean()
    assert not folder.exists()


# ---------- Destination handler ----------


def test_destination_handler_detects_types(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    handler = DestinationHandler("rest:https://example.com")
    assert handler.destination_type == "restic_rest_server"

    existing = tmp_path / "data"
    existing.mkdir()
    handler2 = DestinationHandler(str(existing))
    assert handler2.destination_type == "abs_path"

    handler3 = DestinationHandler("volume-label")
    assert handler3.destination_type == "volume"


def test_destination_handler_mount_and_unmount(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    mountpoints = [str(tmp_path)]

    class DummyMount:
        def __init__(self) -> None:
            self.mounted = False

        def mount(self, destination):  # noqa: ANN001
            self.mounted = True
            return True

        def get_mountpoint(self, destination):  # noqa: ANN001
            return mountpoints

        def unmount(self, destination):  # noqa: ANN001
            mountpoints.clear()

    handler = DestinationHandler("volume-label")
    handler.mounter = DummyMount()

    path = handler.mount()
    assert path.rstrip(os.sep) == str(tmp_path)
    handler.unmount()
    assert mountpoints == []


# ---------- Restic / Rsync wrappers ----------


def test_restic_run_and_backup(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[str] = []
    monkeypatch.setattr(
        "bare.bare.restic.execute_command",
        lambda cmd, env=None, mask=None, ignore_error=False: commands.append(cmd),  # noqa: ARG005
    )
    monkeypatch.setattr("platform.system", lambda: "Linux")
    restic = Restic(
        "/repo", "pw", hostname="host", name="n", check_hostname=False, runner="restic"
    )
    restic.run("snapshots", args={"tag": "weekly"}, dry_run=True)
    restic.backup("/src", args={"exclude": "x"}, mask=None, dry_run=False)
    assert commands  # dry_run still logs command string in our stub


def test_rsync_backup_builds_command(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "bare.bare.rsync.execute_command_test",
        lambda cmd, env=None, mask=None: calls.append(cmd),  # noqa: ARG005
    )
    rsync = Rsync("/dest", hostname="host", name="n", check_hostname=False)
    rsync.run("/src", args={"delete": ""}, dry_run=True)
    rsync.backup("/src", args={}, delete=True, ignore_error=True, dry_run=False)
    assert calls


# ---------- Restic command dispatch ----------


def test_run_restic_command_dry_run(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("INFO")
    configs = {
        "one": {
            "destination": "/dest",
            "restic": {
                "password": "pw",
                "restic_folder": "",
                "runner": "restic",
                "bin_path": None,
                "enable": True,
            },
            "rsync": {"enable": False},
            "mask": None,
            "source": ["s"],
            "check_hostname": False,
            "hostname": "h",
        }
    }
    cli_main.run_restic_command(configs, "snapshots", dry_run=True)
    assert "[dry-run]" in caplog.text


def test_run_restic_command_executes(monkeypatch: pytest.MonkeyPatch) -> None:
    configs = {
        "one": {
            "destination": "/dest",
            "restic": {
                "password": "pw",
                "restic_folder": "",
                "runner": "restic",
                "bin_path": None,
                "enable": True,
            },
            "rsync": {"enable": False},
            "mask": None,
            "source": ["s"],
            "check_hostname": False,
            "hostname": "h",
        }
    }

    class DummyHandler:
        def __init__(self, dest):  # noqa: ANN001
            self.destination = dest
            self.destination_type = "abs_path"

        def __enter__(self):  # noqa: D401
            return "/mnt/dest"

        def __exit__(self, exc_type, exc, tb):  # noqa: D401
            return False

    class DummyRestic:
        def __init__(self, *args, **kwargs):  # noqa: ANN001
            self.commands: list[str] = []

        def run(self, cmd):  # noqa: ANN001
            self.commands.append(cmd)
            return "ok"

    monkeypatch.setattr(cli_main, "DestinationHandler", lambda dest: DummyHandler(dest))
    monkeypatch.setattr(
        cli_main,
        "get_restic_instance",
        lambda config, destination_path, name, destination_type=None: DummyRestic(),  # noqa: ARG005
    )

    cli_main.run_restic_command(configs, "snapshots", dry_run=False)


# ---------- Backup flow ----------


def test_backup_dry_run(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("INFO")
    configs = {
        "one": {
            "destination": "/dest",
            "restic": {
                "enable": True,
                "password": "pw",
                "restic_folder": "",
                "runner": "restic",
                "bin_path": None,
                "args": {},
            },
            "rsync": {"enable": True, "args": {}, "rsync_folder": "rsync"},
            "mask": None,
            "source": ["src"],
            "check_hostname": False,
            "hostname": "h",
        }
    }
    cli_main.backup(configs, dry_run=True, assume_yes=False)
    assert "Dry-run" in caplog.text


def test_backup_executes_restic_and_rsync(monkeypatch: pytest.MonkeyPatch) -> None:
    configs = {
        "one": {
            "destination": "/dest",
            "restic": {
                "enable": True,
                "password": "pw",
                "restic_folder": "",
                "runner": "restic",
                "bin_path": None,
                "args": {},
                "skip-maintain": True,
            },
            "rsync": {"enable": True, "args": {}, "rsync_folder": "rsync"},
            "mask": None,
            "source": ["src"],
            "check_hostname": False,
            "hostname": "h",
        }
    }

    class DummyHandler:
        destination_type = "abs_path"

        def __init__(self, dest):  # noqa: ANN001
            self.dest = dest

        def __enter__(self):  # noqa: D401
            return "/mnt/dest"

        def __exit__(self, exc_type, exc, tb):  # noqa: D401
            return False

    class DummyRestic:
        def __init__(self, *args, **kwargs):  # noqa: ANN001
            self.calls: list[tuple] = []

        def backup(self, source, args, mask=None, dry_run=False):  # noqa: ANN001
            self.calls.append((source, args, mask, dry_run))

    class DummyRsync:
        def __init__(self, *args, **kwargs):  # noqa: ANN001
            self.calls: list[tuple] = []

        def backup(self, source, args, mask=None, dry_run=False):  # noqa: ANN001
            self.calls.append((source, args, mask, dry_run))

    monkeypatch.setattr(cli_main, "DestinationHandler", lambda dest: DummyHandler(dest))
    monkeypatch.setattr(
        cli_main,
        "get_restic_instance",
        lambda config, destination_path, name, destination_type=None: DummyRestic(),  # noqa: ARG005
    )
    monkeypatch.setattr(
        cli_main,
        "get_rsync_instance",
        lambda config, destination_path, name: DummyRsync(),  # noqa: ARG005
    )

    cli_main.backup(configs, dry_run=False, assume_yes=True)


# ---------- Maintenance ----------


def test_post_backup_restic_runs_actions(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO")
    actions: list[str] = []

    class DummyRestic:
        def forget(self, opts):  # noqa: ANN001
            actions.append(f"forget:{opts}")

        def check(self, opts):  # noqa: ANN001
            actions.append(f"check:{opts}")

    config = {
        "restic": {
            "skip-maintain": False,
            "forget": {"keep-last": 1},
            "check": {"read-data-subset": "1/10"},
        }
    }

    cli_main.post_backup_restic(DummyRestic(), config, dry_run=False)
    assert "forget" in actions[0]
    assert "check" in actions[1]


def test_maintain_runs_restic(monkeypatch: pytest.MonkeyPatch) -> None:
    configs = {
        "one": {
            "destination": "/dest",
            "restic": {
                "enable": True,
                "password": "pw",
                "restic_folder": "",
                "runner": "restic",
                "bin_path": None,
                "skip-maintain": False,
                "forget": {},
                "check": {},
            },
            "rsync": {"enable": False},
            "mask": None,
            "source": ["s"],
            "check_hostname": False,
            "hostname": "h",
        }
    }

    class DummyHandler:
        destination_type = "abs_path"

        def __init__(self, dest):  # noqa: ANN001
            self.dest = dest

        def __enter__(self):  # noqa: D401
            return "/mnt"

        def __exit__(self, exc_type, exc, tb):  # noqa: D401
            return False

    class DummyRestic:
        def __init__(self, *args, **kwargs):  # noqa: ANN001
            self.checked = True

        def forget(self, opts):  # noqa: ANN001
            self.checked = True

        def check(self, opts):  # noqa: ANN001
            self.checked = True

    monkeypatch.setattr(cli_main, "DestinationHandler", lambda dest: DummyHandler(dest))
    monkeypatch.setattr(
        cli_main,
        "get_restic_instance",
        lambda config, destination_path, name, destination_type=None: DummyRestic(),  # noqa: ARG005
    )
    cli_main.maintain(configs)


# ---------- Umount ----------


def test_umount_calls_mount_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"umount": False, "clean": False}

    class DummyMountManager:
        def umount_all(self):  # noqa: ANN001
            called["umount"] = True

        def clean(self):  # noqa: ANN001
            called["clean"] = True

    monkeypatch.setattr(cli_main, "MountManager", lambda: DummyMountManager())
    cli_main.umount()
    assert called["umount"] and called["clean"]


# ---------- Finders and utils ----------


def test_device_finder_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    finder = DeviceFinder()
    monkeypatch.setattr(
        finder,
        "get_all_devices",
        lambda: [{"name": "sda1", "label": "backup", "mountpoints": ["/mnt"]}],
    )
    assert finder.find_device(name="sda1")
    assert finder.find_device(label="backup")
    assert finder.find_device(path="/mnt")


def test_dict2args_and_modify_command_for_os(monkeypatch: pytest.MonkeyPatch) -> None:
    args = dict2args({"flag": "", "list": [1, 2]})
    assert "--flag" in args and "--list 1" in args and "--list 2" in args

    monkeypatch.setattr("platform.system", lambda: "Linux")
    masked = modify_command_for_os("echo hi", mask=["/real", "/masked"])
    assert masked == "proot -b /real:/masked echo hi"


def test_base_confirm_hostname_prompts(monkeypatch: pytest.MonkeyPatch) -> None:
    from bare.bare.base import Base

    monkeypatch.setattr("bare.bare.base.get_hostname", lambda: "current")
    monkeypatch.setattr("builtins.input", lambda prompt: "y")  # noqa: ARG005
    base = Base(hostname="other", name="n", check_hostname=True)
    assert base.hostname == "other"


def test_parse_mount_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    from bare import utils

    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(
        "bare.utils.execute_command",
        lambda cmd: "/dev/sda1 on / type ext4 (rw,relatime)\n",  # noqa: ARG005
    )
    mounts = utils.parse_mount()
    assert mounts[0]["src"] == "/dev/sda1"


def test_drive_finder_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    sample = {
        "blockdevices": [
            {"name": "sda", "label": "LBL", "mountpoints": ["/mnt"], "fstype": "ext4"}
        ]
    }
    monkeypatch.setattr(
        "bare.finder.physical.execute_command",
        lambda cmd: json.dumps(sample),  # noqa: ARG005
    )
    finder = DriveFinderLinux()
    devices = finder.get_physical_drives()
    assert devices[0]["name"] == "sda"


def test_drive_finder_darwin(monkeypatch: pytest.MonkeyPatch) -> None:
    plist_content = {
        "AllDisksAndPartitions": [
            {
                "DeviceIdentifier": "disk1",
                "VolumeName": "Main",
                "MountPoint": "/Volumes/Main",
                "Content": "apfs",
            }
        ]
    }
    monkeypatch.setattr(
        "bare.finder.physical.execute_command",
        lambda cmd: plist_dumps(plist_content),  # noqa: ARG005
    )
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    finder = DriveFinderDarwin()
    devices = finder.get_physical_drives()
    assert devices[0]["name"] == "disk1"


def plist_dumps(obj):  # type: ignore[override]
    import plistlib

    return plistlib.dumps(obj).decode()


def test_rclone_finder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "bare.finder.rclone.execute_command",
        lambda cmd: "remote:\n",  # noqa: ARG005
    )
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(
        RcloneFinder,
        "get_rclone_mountpoint_unix",
        lambda self: {"remote:": "/mnt/remote"},  # noqa: ARG005
    )

    finder = RcloneFinder()
    drives = finder.get_drives()
    assert drives[0]["mountpoints"][0] == "/mnt/remote"


def test_gocryptfs_finder(monkeypatch: pytest.MonkeyPatch) -> None:
    from bare.finder.gocryptfs import GocryptfsFinder

    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(
        "bare.finder.gocryptfs.parse_mount",
        lambda: [
            {
                "src": "/enc",
                "dest": "/dec",
                "fstype": "fuse.gocryptfs",
                "args": "",
            }
        ],
    )

    drives = GocryptfsFinder().get_drives()
    assert drives[0]["label"] == "/enc"
