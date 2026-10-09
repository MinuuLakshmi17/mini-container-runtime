"""Configuration validation for mini-container-runtime."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class Limits:
    memory_max: int | None = None
    pids_max: int | None = None
    cpu_quota_us: int | None = None
    cpu_period_us: int = 100_000

    def validate(self) -> None:
        for name in ("memory_max", "pids_max", "cpu_quota_us", "cpu_period_us"):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True)
class RunSpec:
    rootfs: Path
    command: tuple[str, ...]
    hostname: str = "mini-container"
    limits: Limits = Limits()

    def validate(self) -> None:
        if not self.command or not self.command[0]:
            raise ValueError("command must contain an executable")
        if not self.hostname or "/" in self.hostname or "\x00" in self.hostname:
            raise ValueError("hostname must be a non-empty simple name")
        if not self.rootfs.exists() or not self.rootfs.is_dir():
            raise ValueError(f"rootfs is not a directory: {self.rootfs}")
        if not (self.rootfs / "bin").exists() and not (self.rootfs / "usr").exists():
            raise ValueError("rootfs does not look like a Linux filesystem (expected bin/ or usr/)")
        self.limits.validate()


def load_spec(path: str | Path) -> RunSpec:
    """Load a JSON spec (YAML is intentionally not a dependency)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    limits_data = data.get("limits", {})
    spec = RunSpec(
        rootfs=Path(data["rootfs"]).resolve(),
        command=tuple(data["command"]),
        hostname=data.get("hostname", "mini-container"),
        limits=Limits(**limits_data),
    )
    spec.validate()
    return spec
