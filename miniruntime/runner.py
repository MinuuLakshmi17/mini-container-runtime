"""Linux namespace/chroot launcher. Real execution is deliberately opt-in."""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
from pathlib import Path
from .config import RunSpec
from .cgroups import CgroupV2, CgroupError


class RuntimeErrorMini(RuntimeError):
    pass


def build_command(spec: RunSpec) -> list[str]:
    """Build command invoking util-linux unshare and this package's child helper."""
    unshare = shutil.which("unshare")
    if not unshare:
        raise RuntimeErrorMini("'unshare' not found; install util-linux")
    helper = str(Path(__file__).with_name("_child.py"))
    # Note: no --mount-proc here. Proc must be mounted AFTER chroot (the child
    # helper does it via mount(2)); mounting before chroot places proc at the
    # host's /proc, which becomes unreachable once the root changes.
    # No host paths are bind-mounted.
    return [unshare, "--mount", "--uts", "--ipc", "--pid", "--fork",
            sys.executable, helper, str(spec.rootfs), spec.hostname, "--", *spec.command]


def run(spec: RunSpec, *, dry_run: bool = False, use_cgroups: bool = False,
        cgroup_root: Path = Path("/sys/fs/cgroup")) -> int:
    spec.validate()
    command = build_command(spec)
    if dry_run:
        print("Dry run; no process launched:")
        print(" ".join(repr(x) for x in command))
        if use_cgroups:
            print(f"cgroups v2 limits requested: {spec.limits}")
        return 0
    if not sys.platform.startswith("linux"):
        raise RuntimeErrorMini("this runtime only works on Linux")
    if os.geteuid() != 0:
        raise RuntimeErrorMini("real chroot execution requires root; use --dry-run to inspect the command")

    cg = None
    proc = None
    try:
        if use_cgroups:
            cg = CgroupV2("run", cgroup_root)
            cg.create(memory_max=spec.limits.memory_max, pids_max=spec.limits.pids_max,
                      cpu_quota_us=spec.limits.cpu_quota_us, cpu_period_us=spec.limits.cpu_period_us)
        proc = subprocess.Popen(command)
        if cg:
            cg.attach(proc.pid)
        return proc.wait()
    except (OSError, CgroupError) as exc:
        if proc and proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=3)
        raise RuntimeErrorMini(str(exc)) from exc
    finally:
        if cg:
            try:
                cg.remove()
            except CgroupError:
                # A surviving child may keep the cgroup busy; do not hide its location.
                print(f"warning: {cg.path} could not be removed; inspect remaining processes", file=sys.stderr)
