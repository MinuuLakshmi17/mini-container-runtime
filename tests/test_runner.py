from pathlib import Path
from miniruntime.config import RunSpec
from miniruntime.runner import build_command


def test_command_uses_expected_namespaces(tmp_path):
    (tmp_path / "bin").mkdir()
    spec = RunSpec(tmp_path, ("/bin/sh", "-c", "true"))
    cmd = build_command(spec)
    joined = " ".join(cmd)
    for flag in ("--mount", "--uts", "--ipc", "--pid", "--fork"):
        assert flag in joined
    # Proc is mounted by the child helper AFTER chroot (mounting before
    # chroot would place it at the host's /proc, unreachable post-chroot).
    assert "--mount-proc" not in joined
    assert "_child.py" in joined
