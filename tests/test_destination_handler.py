import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bare.destination_handler import DestinationHandler


def test_detect_destination_type_restic():
    dh = DestinationHandler("rest:https://example.com")
    assert dh.destination_type == "restic_rest_server"


def test_detect_destination_type_volume():
    dh = DestinationHandler("myvolume")
    assert dh.destination_type == "volume"


def test_check_abs_path(tmp_path: Path):
    path = tmp_path / "data"
    path.mkdir()
    dh = DestinationHandler(str(path))
    assert dh.destination_type == "abs_path"
    assert dh._check_abs_path() == str(path)
    with pytest.raises(FileExistsError):
        DestinationHandler(str(path / "missing"))._check_abs_path()
