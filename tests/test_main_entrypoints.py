from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

import bare.main as cli_main


def test_build_parser_includes_commands() -> None:
    parser = cli_main.build_parser()
    commands = parser._subparsers._group_actions[0].choices  # type: ignore[attr-defined]
    for cmd in ["backup", "restic", "snapshots", "umount", "list", "maintain"]:
        assert cmd in commands


def test_resolve_session_path_prefers_cli(tmp_path: Path) -> None:
    session = tmp_path / "session.yml"
    session.write_text("default: {}\n")

    resolved = cli_main.resolve_session_path(str(session))
    assert resolved == session.resolve()


def test_resolve_session_path_env(tmp_path: Path) -> None:
    session = tmp_path / "session.yml"
    session.write_text("default: {}\n")
    env = {cli_main.DEFAULT_SESSION_ENV_VAR: str(session)}

    resolved = cli_main.resolve_session_path(None, env=env)
    assert resolved == session.resolve()


def test_load_session_validates_yaml(tmp_path: Path) -> None:
    session = tmp_path / "session.yml"
    session.write_text("default: {}\n")
    data = cli_main.load_session(session)
    assert "default" in data


def test_load_session_raises_for_missing(tmp_path: Path) -> None:
    session = tmp_path / "missing.yml"
    with pytest.raises(FileNotFoundError):
        cli_main.load_session(session)


def test_build_cli_config_none_when_no_destination() -> None:
    args = argparse.Namespace(destination=None)
    assert cli_main.build_cli_config(args, "backup") is None


def test_main_no_command_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    parser = cli_main.build_parser()
    monkeypatch.setattr(cli_main, "build_parser", lambda: parser)
    monkeypatch.setattr(sys, "argv", ["bare"])
    with pytest.raises(SystemExit):
        cli_main.main()
    out = capsys.readouterr()
    assert "usage" in out.err or "usage" in out.out


def test_main_umount_calls_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = cli_main.build_parser()
    monkeypatch.setattr(cli_main, "build_parser", lambda: parser)
    monkeypatch.setattr(sys, "argv", ["bare", "umount"])
    called = {"umount": False}

    def fake_umount():  # noqa: D401
        called["umount"] = True

    monkeypatch.setattr(cli_main, "umount", fake_umount)
    cli_main.main()
    assert called["umount"] is True


def test_main_missing_session_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = cli_main.build_parser()
    monkeypatch.setattr(cli_main, "build_parser", lambda: parser)
    monkeypatch.setattr(sys, "argv", ["bare", "backup", "--session", "missing.yml"])
    with pytest.raises(SystemExit):
        cli_main.main()
