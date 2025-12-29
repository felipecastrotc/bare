from __future__ import annotations

import os
import stat
from types import SimpleNamespace

import pytest

from bare.mount.base import MountBase
from bare.mount.drive import MountDrive
from bare.mount.gocryptfs import MountGocryptfs
from bare.mount.physical import MountDriveDarwin, MountDriveLinux, MountDrivePhysical
from bare.mount.rclone import MountDriveRclone


class DummyFinder:
    def __init__(self, devices: list[dict] | dict) -> None:
        # Accept a single dict for convenience in tests.
        self.devices = devices

    def find_device(self, label=None, name=None, path=None):  # noqa: ANN001
        if isinstance(self.devices, dict):
            return [self.devices]
        return self.devices


def test_generate_temporary_directory_secure_permissions() -> None:
    base = MountBase()
    path = base.generate_temporary_directory()

    assert base.prefix in path
    assert os.path.exists(path)
    assert stat.S_IMODE(os.stat(path).st_mode) == stat.S_IRWXU

    os.rmdir(path)


def test_generate_temporary_directory_symbolic_cleanup() -> None:
    base = MountBase()
    path = base.generate_temporary_directory(symbolic=True)

    assert base.prefix in path
    assert not os.path.exists(path)


def test_clean_device_temporary_directory_requires_identifier() -> None:
    base = MountBase()

    with pytest.raises(ValueError):
        base.clean_device_temporary_directory()


def test_clean_device_temporary_directory_removes_mountpoints(tmp_path) -> None:  # noqa: ANN001
    base = MountBase()
    mount_dir = tmp_path / "BUP.tmp.test"
    mount_dir.mkdir()

    base.clean_device_temporary_directory(
        device={"mountpoints": [str(mount_dir)]}, path=None
    )

    assert not mount_dir.exists()


def test_get_device_validates_presence(monkeypatch) -> None:
    base = MountBase()
    monkeypatch.setattr(base, "finder", DummyFinder([]))

    with pytest.raises(ValueError):
        base.get_device(label="missing")


def test_get_device_returns_single_match(monkeypatch) -> None:
    device = {"name": "sda1", "label": "backup"}
    base = MountBase()
    monkeypatch.setattr(base, "finder", DummyFinder([device]))

    result = base.get_device(label="backup")

    assert result == device


def test_mount_drive_dispatches_rclone(monkeypatch) -> None:
    device = {"fstype": "fuse.rclone"}
    drive = MountDrive()
    monkeypatch.setattr(drive, "get_device", lambda **_: device)

    calls: list[dict] = []

    class DummyRclone:
        def mount(self, device):  # noqa: ANN001
            calls.append(device)
            return "mounted"

    monkeypatch.setattr("bare.mount.drive.MountDriveRclone", lambda: DummyRclone())

    assert drive.mount(label="remote") == "mounted"
    assert calls == [device]


def test_mount_drive_dispatches_physical(monkeypatch) -> None:
    device = {"fstype": "ext4"}
    drive = MountDrive()
    monkeypatch.setattr(drive, "get_device", lambda **_: device)

    calls: list[dict] = []

    class DummyPhysical:
        def mount(self, device):  # noqa: ANN001
            calls.append(device)
            return True

    monkeypatch.setattr("bare.mount.drive.MountDrivePhysical", lambda: DummyPhysical())

    assert drive.mount(device_name="sda1")
    assert calls == [device]


def test_unmount_drive_routes_by_fstype(monkeypatch) -> None:
    device = {"fstype": "ext4"}
    drive = MountDrive()
    monkeypatch.setattr(drive, "get_device", lambda **_: device)

    calls: list[str | None] = []

    class DummyPhysical:
        def unmount(self, device, path=None):  # noqa: ANN001, D401
            calls.append(path)

    monkeypatch.setattr("bare.mount.drive.MountDrivePhysical", lambda: DummyPhysical())

    drive.unmount(device_name="sda1", path="/mnt/drive")
    assert calls == ["/mnt/drive"]


def test_physical_mount_invokes_os_helper(monkeypatch) -> None:
    device = {"name": "sda1", "mountpoints": []}
    calls: list[str] = []

    class DummyMounter:
        def mount(self, name):  # noqa: ANN001
            calls.append(name)

    physical = MountDrivePhysical()
    monkeypatch.setattr(physical, "finder", DummyFinder(device))
    monkeypatch.setattr(physical, "_get_mounter", lambda: DummyMounter())

    assert physical.mount(name="sda1") is True
    assert calls == ["sda1"]


def test_physical_mount_skips_when_already_mounted(monkeypatch) -> None:
    device = {"name": "sda1", "mountpoints": ["/mnt/drive"]}
    physical = MountDrivePhysical()
    monkeypatch.setattr(physical, "finder", DummyFinder(device))

    assert physical.mount(name="sda1") is False


def test_physical_unmount_resolves_path_and_cleans(monkeypatch, tmp_path) -> None:  # noqa: ANN001
    mountpoint = tmp_path / "BUP.tmp.drive"
    mountpoint.mkdir()
    device = {"name": "sda1", "mountpoints": [str(mountpoint)]}
    unmounted: list[str] = []
    cleaned: list[str] = []

    class DummyMounter:
        def unmount(self, path):  # noqa: ANN001
            unmounted.append(path)

    physical = MountDrivePhysical()
    monkeypatch.setattr(physical, "finder", DummyFinder(device))
    monkeypatch.setattr(physical, "_get_mounter", lambda: DummyMounter())
    monkeypatch.setattr(
        physical,
        "clean_device_temporary_directory",
        lambda device=None, path=None: cleaned.append(path or ""),  # noqa: ARG001
    )

    physical.unmount(name="sda1")

    assert unmounted == [str(mountpoint)]
    assert cleaned == [str(mountpoint)]


def test_physical_unmount_requires_identifier() -> None:
    physical = MountDrivePhysical()

    with pytest.raises(ValueError):
        physical.unmount()


@pytest.mark.parametrize(
    "os_name,expected_type",
    [
        ("Linux", MountDriveLinux),
        ("Darwin", MountDriveDarwin),
    ],
)
def test_get_mounter_selects_supported_os(monkeypatch, os_name, expected_type) -> None:  # noqa: ANN001
    physical = MountDrivePhysical()
    monkeypatch.setattr("platform.system", lambda: os_name)

    mounter = physical._get_mounter()

    assert isinstance(mounter, expected_type)


def test_rclone_mount_creates_temp_and_runs_command(monkeypatch, tmp_path) -> None:  # noqa: ANN001
    device = {"label": "remote", "mountpoints": []}
    commands: list[str] = []

    def fake_temp_dir(self):  # noqa: ANN001
        path = tmp_path / "BUP.tmp.rclone"
        path.mkdir()
        return str(path)

    monkeypatch.setattr(MountDriveRclone, "generate_temporary_directory", fake_temp_dir)
    monkeypatch.setattr(
        "bare.mount.rclone.execute_command", lambda cmd: commands.append(cmd)
    )

    rclone = MountDriveRclone()
    assert rclone.mount(device=device) is True

    assert commands == [
        "rclone mount remote " + str(tmp_path / "BUP.tmp.rclone") + " --daemon"
    ]


def test_rclone_mount_returns_false_when_already_mounted(monkeypatch) -> None:
    device = {"label": "remote", "mountpoints": ["/mnt/remote"]}
    rclone = MountDriveRclone()
    executed: list[str] = []
    monkeypatch.setattr(
        "bare.mount.rclone.execute_command",
        lambda cmd: executed.append(cmd),  # noqa: ARG001
    )

    assert rclone.mount(device=device) is False
    assert executed == []


def test_rclone_unmount_uses_system_umount(monkeypatch, tmp_path) -> None:  # noqa: ANN001
    mountpoint = tmp_path / "BUP.tmp.rclone"
    mountpoint.mkdir()
    device = {"label": "remote", "mountpoints": [str(mountpoint)]}

    commands: list[str] = []
    cleaned: list[str] = []

    rclone = MountDriveRclone()
    monkeypatch.setattr(rclone, "finder", DummyFinder(device))
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(
        "bare.mount.rclone.execute_command", lambda cmd: commands.append(cmd)
    )
    monkeypatch.setattr(
        rclone,
        "clean_device_temporary_directory",
        lambda device=None, path=None: cleaned.append(path or ""),  # noqa: ARG001
    )

    rclone.unmount(label="remote")

    assert commands == [f"umount {mountpoint}"]
    assert cleaned == [str(mountpoint)]


def test_rclone_unmount_rejects_unsupported_os(monkeypatch) -> None:
    rclone = MountDriveRclone()
    monkeypatch.setattr("platform.system", lambda: "Windows")

    with pytest.raises(NotImplementedError):
        rclone.unmount(path="/mnt/remote")


def test_gocryptfs_mount_success(monkeypatch, tmp_path) -> None:  # noqa: ANN001
    commands: list[str] = []
    mounts: list[str] = []

    def fake_execute(cmd, env=None):  # noqa: ANN001
        commands.append((cmd, env))

    def fake_temp_dir(self):  # noqa: ANN001
        path = tmp_path / "BUP.tmp.gocryptfs"
        path.mkdir()
        return str(path)

    mount_helper = MountGocryptfs(path="encrypted", gocryptfs_password="pw")
    mount_helper.env = {}
    mount_helper.gofs = SimpleNamespace(
        path=None, mount=lambda dest: mounts.append(dest)
    )
    monkeypatch.setattr(mount_helper, "finder", DummyFinder([]))
    monkeypatch.setattr("bare.mount.gocryptfs.execute_command", fake_execute)
    monkeypatch.setattr(MountGocryptfs, "generate_temporary_directory", fake_temp_dir)

    assert mount_helper.mount(label="encrypted") is True
    assert commands == [("gocryptfs -info encrypted", {})]
    assert mounts == [str(tmp_path / "BUP.tmp.gocryptfs")]


def test_gocryptfs_mount_invalid_repository(monkeypatch) -> None:
    mount_helper = MountGocryptfs(path="encrypted", gocryptfs_password="pw")
    mount_helper.env = {}
    mount_helper.gofs = SimpleNamespace(path=None, mount=lambda dest: None)  # noqa: ARG005
    monkeypatch.setattr(mount_helper, "finder", DummyFinder([]))

    def raise_failure(*_, **__) -> None:
        raise Exception("bad")

    monkeypatch.setattr("bare.mount.gocryptfs.execute_command", raise_failure)

    assert mount_helper.mount(label="encrypted") is False


def test_gocryptfs_unmount_invokes_umount_and_cleans(monkeypatch, tmp_path) -> None:  # noqa: ANN001
    mountpoint = tmp_path / "BUP.tmp.gocryptfs"
    mountpoint.mkdir()
    device = {"mountpoints": [str(mountpoint)]}
    commands: list[str] = []
    cleaned: list[str] = []

    mount_helper = MountGocryptfs(path="encrypted", gocryptfs_password="pw")
    mount_helper.env = {}
    monkeypatch.setattr(mount_helper, "finder", DummyFinder(device))
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(
        "bare.mount.gocryptfs.execute_command", lambda cmd: commands.append(cmd)
    )
    monkeypatch.setattr(
        mount_helper,
        "clean_device_temporary_directory",
        lambda device=None, path=None: cleaned.append(path or ""),  # noqa: ARG001
    )

    mount_helper.unmount(label="encrypted")

    assert commands == [f"umount {mountpoint}"]
    assert cleaned == [str(mountpoint)]
