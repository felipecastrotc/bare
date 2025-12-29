from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bare.main import (
    collect_missing_dependencies,
    normalize_config,
    resolve_session_path,
)


def test_resolve_session_path_prefers_cli(tmp_path: Path) -> None:
    session = tmp_path / "session.yml"
    session.write_text("default: {}\n")

    resolved = resolve_session_path(str(session))
    assert resolved == session.resolve()


def test_resolve_session_path_uses_env(tmp_path: Path) -> None:
    session = tmp_path / "env_session.yml"
    session.write_text("default: {}\n")

    resolved = resolve_session_path(None, env={"BARE_SESSION": str(session)})
    assert resolved == session.resolve()


def test_resolve_session_path_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yml"
    with pytest.raises(FileNotFoundError):
        resolve_session_path(str(missing))


def test_collect_missing_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    import bare.main as main

    monkeypatch.setattr(
        main, "is_executable_available", lambda name: name not in {"restic", "rsync"}
    )
    configs = {
        "target": normalize_config(
            {
                "destination": "/tmp/backup",
                "restic": {"enable": True},
                "rsync": {"enable": True},
            }
        )
    }

    missing = collect_missing_dependencies(configs)
    assert missing == ["restic", "rsync"]
