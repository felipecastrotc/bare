from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from bare.scripts import schedule_runner as runner


def _config(tmp_path: Path) -> runner.Config:
    return runner.Config(
        bare_bin=Path("/opt/bare/bare"),
        log_file=tmp_path / "bare.log",
        state_file=tmp_path / "last_success.txt",
        server_host="restic.local",
        server_port=80,
        tailscale_bin=tmp_path / "missing-tailscale",
    )


def test_perform_backup_skips_confirmation_prompt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    runner.perform_backup(_config(tmp_path))

    assert calls == [["/opt/bare/bare", "backup", "--yes"]]


def test_failed_backup_is_not_recorded_as_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = _config(tmp_path)

    def failing_run(cmd: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            cmd, returncode=1, stdout="Proceed with backup? [y/N]: ", stderr="EOFError"
        )

    monkeypatch.setattr(runner, "load_config", lambda: config)
    monkeypatch.setattr(runner, "setup_logging", lambda _log_file: None)
    monkeypatch.setattr(runner, "check_port", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(runner.subprocess, "run", failing_run)

    assert runner.main() == 1
    assert config.state_file.read_text().endswith("FAILURE")
