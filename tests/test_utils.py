from __future__ import annotations

import platform
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bare.utils import build_command, dict2args, modify_command_for_os


def test_build_command() -> None:
    assert build_command("echo", "hi", 1) == "echo hi 1"


def test_dict2args() -> None:
    args = {"exclude": "/tmp", "I": ["a", "b"]}
    result = dict2args(args)
    assert "--exclude /tmp" in result
    assert "-I a" in result
    assert "-I b" in result


def test_modify_command_for_os_linux_with_mask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    cmd = modify_command_for_os("ls", ["src", "dst"])
    assert cmd == "proot -b src:dst ls"
