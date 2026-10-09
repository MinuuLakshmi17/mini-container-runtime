import json
from pathlib import Path
import pytest
from miniruntime.config import Limits, RunSpec, load_spec


def test_load_spec(tmp_path):
    (tmp_path / "bin").mkdir()
    f = tmp_path / "spec.json"
    f.write_text(json.dumps({"rootfs": str(tmp_path), "command": ["/bin/sh"], "limits": {"pids_max": 20}}))
    spec = load_spec(f)
    assert spec.command == ("/bin/sh",)
    assert spec.limits.pids_max == 20


def test_rejects_missing_rootfs():
    with pytest.raises(ValueError, match="not a directory"):
        RunSpec(Path("/not/a/real/rootfs"), ("/bin/sh",)).validate()


def test_rejects_invalid_limits(tmp_path):
    (tmp_path / "bin").mkdir()
    with pytest.raises(ValueError, match="positive"):
        RunSpec(tmp_path, ("/bin/sh",), limits=Limits(pids_max=0)).validate()


def test_rejects_bad_hostname(tmp_path):
    (tmp_path / "bin").mkdir()
    with pytest.raises(ValueError, match="hostname"):
        RunSpec(tmp_path, ("/bin/sh",), hostname="bad/name").validate()
