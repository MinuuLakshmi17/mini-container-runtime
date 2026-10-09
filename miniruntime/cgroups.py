"""Small cgroups v2 helper. Requires a delegated writable cgroup subtree."""
from __future__ import annotations
from pathlib import Path
import os
import re


class CgroupError(RuntimeError):
    pass


def _write(path: Path, value: str) -> None:
    try:
        path.write_text(value, encoding="ascii")
    except OSError as exc:
        raise CgroupError(f"cannot write {path}: {exc}. Is cgroups v2 mounted and this subtree delegated?") from exc


class CgroupV2:
    def __init__(self, name: str, root: Path = Path("/sys/fs/cgroup")):
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", name):
            raise ValueError("unsafe cgroup name")
        self.path = root / f"mini-container-{name}-{os.getpid()}"
        self.root = root

    def create(self, *, memory_max: int | None, pids_max: int | None,
               cpu_quota_us: int | None, cpu_period_us: int) -> None:
        if not (self.root / "cgroup.controllers").exists():
            raise CgroupError("cgroups v2 not detected at /sys/fs/cgroup")
        try:
            self.path.mkdir()
        except OSError as exc:
            raise CgroupError(f"cannot create cgroup {self.path}: {exc}") from exc
        try:
            if memory_max is not None:
                _write(self.path / "memory.max", str(memory_max))
            if pids_max is not None:
                _write(self.path / "pids.max", str(pids_max))
            if cpu_quota_us is not None:
                _write(self.path / "cpu.max", f"{cpu_quota_us} {cpu_period_us}")
        except Exception:
            self.remove()
            raise

    def attach(self, pid: int) -> None:
        _write(self.path / "cgroup.procs", str(pid))

    def remove(self) -> None:
        try:
            self.path.rmdir()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise CgroupError(f"could not remove cgroup {self.path}: {exc}") from exc
