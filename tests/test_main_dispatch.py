from __future__ import annotations

import sys
from pathlib import Path

import pytest

import bare.main as cli_main


def _base_session():
    return {
        "t": {
            "destination": "/dest",
            "restic": {
                "password": "pw",
                "enable": True,
                "restic_folder": "",
                "runner": "restic",
                "bin_path": None,
                "args": {},
            },
            "rsync": {"enable": False, "args": {}, "rsync_folder": "rsync"},
            "mask": None,
            "source": ["s"],
            "check_hostname": False,
            "hostname": "h",
        }
    }


def test_main_dependency_failure_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = cli_main.build_parser()
    monkeypatch.setattr(cli_main, "build_parser", lambda: parser)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "bare",
            "backup",
            "--session",
            "s",
            "--destination",
            "/dest",
            "--restic-password",
            "pw",
        ],
    )
    monkeypatch.setattr(cli_main, "resolve_session_path", lambda p: Path("s"))  # noqa: ARG005
    monkeypatch.setattr(cli_main, "load_session", lambda p: {})  # noqa: ARG005
    monkeypatch.setattr(
        cli_main, "collect_missing_dependencies", lambda cfg: ["restic"]
    )  # noqa: ARG005

    with pytest.raises(SystemExit):
        cli_main.main()


def test_main_backup_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = cli_main.build_parser()
    monkeypatch.setattr(cli_main, "build_parser", lambda: parser)
    monkeypatch.setattr(
        sys, "argv", ["bare", "backup", "--session", "s", "--target", "t", "--yes"]
    )
    monkeypatch.setattr(cli_main, "resolve_session_path", lambda p: Path("s"))  # noqa: ARG005
    monkeypatch.setattr(cli_main, "load_session", lambda p: _base_session())  # noqa: ARG005
    monkeypatch.setattr(cli_main, "collect_missing_dependencies", lambda cfg: [])  # noqa: ARG005
    called = {"backup": False}

    def fake_backup(configs, dry_run, assume_yes):  # noqa: ANN001
        called["backup"] = True
        assert assume_yes is True
        assert "t" in configs

    monkeypatch.setattr(cli_main, "backup", fake_backup)
    cli_main.main()
    assert called["backup"] is True


def test_main_restic_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = cli_main.build_parser()
    monkeypatch.setattr(cli_main, "build_parser", lambda: parser)
    monkeypatch.setattr(
        sys, "argv", ["bare", "restic", "--session", "s", "--target", "t", "snapshots"]
    )
    monkeypatch.setattr(cli_main, "resolve_session_path", lambda p: Path("s"))  # noqa: ARG005
    monkeypatch.setattr(cli_main, "load_session", lambda p: _base_session())  # noqa: ARG005
    monkeypatch.setattr(cli_main, "collect_missing_dependencies", lambda cfg: [])  # noqa: ARG005
    called = {"restic": False}

    def fake_run(configs, cmd, dry_run):  # noqa: ANN001
        called["restic"] = True
        assert cmd.startswith("snapshots")
        assert "t" in configs

    monkeypatch.setattr(cli_main, "run_restic_command", fake_run)
    cli_main.main()
    assert called["restic"] is True


def test_main_snapshots_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = cli_main.build_parser()
    monkeypatch.setattr(cli_main, "build_parser", lambda: parser)
    monkeypatch.setattr(sys, "argv", ["bare", "snapshots", "--session", "s"])
    monkeypatch.setattr(cli_main, "resolve_session_path", lambda p: Path("s"))  # noqa: ARG005
    monkeypatch.setattr(cli_main, "load_session", lambda p: _base_session())  # noqa: ARG005
    monkeypatch.setattr(cli_main, "collect_missing_dependencies", lambda cfg: [])  # noqa: ARG005
    called = {"restic": False}
    monkeypatch.setattr(
        cli_main,
        "run_restic_command",
        lambda cfg, cmd, dry_run: called.update(restic=True),
    )  # noqa: ARG005

    cli_main.main()
    assert called["restic"] is True


def test_main_maintain_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = cli_main.build_parser()
    monkeypatch.setattr(cli_main, "build_parser", lambda: parser)
    monkeypatch.setattr(sys, "argv", ["bare", "maintain", "--session", "s"])
    monkeypatch.setattr(cli_main, "resolve_session_path", lambda p: Path("s"))  # noqa: ARG005
    monkeypatch.setattr(cli_main, "load_session", lambda p: _base_session())  # noqa: ARG005
    called = {"maintain": False}
    monkeypatch.setattr(cli_main, "maintain", lambda cfg: called.update(maintain=True))  # noqa: ARG005

    cli_main.main()
    assert called["maintain"] is True
