from pathlib import Path
import pytest
from miniruntime.cgroups import CgroupV2


def test_name_validation(tmp_path):
    with pytest.raises(ValueError):
        CgroupV2("../oops", tmp_path)


def test_writes_requested_limits(tmp_path):
    (tmp_path / "cgroup.controllers").write_text("cpu memory pids")
    cg = CgroupV2("test", tmp_path)
    cg.create(memory_max=1024, pids_max=12, cpu_quota_us=50000, cpu_period_us=100000)
    assert (cg.path / "memory.max").read_text() == "1024"
    assert (cg.path / "pids.max").read_text() == "12"
    assert (cg.path / "cpu.max").read_text() == "50000 100000"
    # Real cgroupfs control files are virtual; remove the test stand-ins first.
    for name in ("memory.max", "pids.max", "cpu.max"):
        (cg.path / name).unlink()
    cg.remove()
