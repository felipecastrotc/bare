from __future__ import annotations

import pytest

from bare.bare.backup import Backup


class StubDestination:
    def __init__(self, path: str = "/mnt/dest") -> None:
        self.path = path
        self.entered = False
        self.exited = False

    def __enter__(self) -> str:
        self.entered = True
        return self.path

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.exited = True
        return False


def test_backup_requires_destination_or_vol_label() -> None:
    with pytest.raises(ValueError):
        Backup("src")


def test_backup_restic_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple] = []

    class FakeRestic:
        def __init__(self, path, password, **kwargs):  # noqa: ANN001, D401
            self.path = path
            self.password = password

        def backup(self, source, args, mask=None, dry_run=False):  # noqa: ANN001
            calls.append((source, args, mask, dry_run))

    storage = StubDestination("/mnt/repo")
    monkeypatch.setattr("bare.bare.backup.Restic", FakeRestic)
    backup = Backup(
        source="/data",
        destination="repo",
        restic_password="pw",
        storage=storage,
    )

    backup.perform_backup(
        use_restic=True,
        restic_args={"exclude": "tmp"},
        mask="mask",
        dry_run=True,
    )

    assert storage.entered and storage.exited
    assert calls == [("/data", {"exclude": "tmp"}, "mask", True)]


def test_backup_rsync_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple] = []

    class FakeRsync:
        def __init__(self, path, **kwargs):  # noqa: ANN001, D401
            self.path = path

        def backup(self, source, args, mask=None, dry_run=False):  # noqa: ANN001
            calls.append((source, args, mask, dry_run))

    storage = StubDestination("/mnt/repo")
    monkeypatch.setattr("bare.bare.backup.Rsync", FakeRsync)
    backup = Backup(
        source="/data",
        destination="repo",
        storage=storage,
    )

    backup.perform_backup(
        use_rsync=True,
        rsync_args={"delete": ""},
        mask=None,
        dry_run=False,
    )

    assert calls == [("/data", {"delete": ""}, None, False)]


def test_backup_handles_mask_list(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple] = []

    class FakeRestic:
        def __init__(self, path, password=None, **kwargs):  # noqa: ANN001, D401
            pass

        def backup(self, source, args, mask=None, dry_run=False):  # noqa: ANN001
            calls.append((source, mask))

    storage = StubDestination("/mnt/repo")
    monkeypatch.setattr("bare.bare.backup.Restic", FakeRestic)
    backup = Backup(
        source="/data",
        destination="repo",
        storage=storage,
    )

    backup.destination = "repo"
    backup.perform_backup(
        use_restic=True,
        restic_args={},
        mask=["m1", "m2"],
        dry_run=False,
    )

    assert calls[0] == ("/data", ["m1", "m2"])


def test_backup_skip_maintain(monkeypatch: pytest.MonkeyPatch) -> None:
    actions: list[str] = []

    class FakeRestic:
        def __init__(self, path, password=None, **kwargs):  # noqa: ANN001, D401
            pass

        def backup(self, source, args, mask=None, dry_run=False):  # noqa: ANN001
            actions.append("backup")

    class FakeRsync:
        def __init__(self, path, **kwargs):  # noqa: ANN001, D401
            pass

        def backup(self, source, args, mask=None, dry_run=False):  # noqa: ANN001
            actions.append("rsync")

    storage = StubDestination("/mnt/repo")
    monkeypatch.setattr("bare.bare.backup.Restic", FakeRestic)
    monkeypatch.setattr("bare.bare.backup.Rsync", FakeRsync)

    backup = Backup(
        source="/data",
        destination="repo",
        storage=storage,
    )
    backup.restic_password = "pw"

    backup.perform_backup(
        use_restic=True,
        use_rsync=True,
        restic_args={},
        rsync_args={},
        dry_run=False,
    )

    assert actions == ["backup", "rsync"]
