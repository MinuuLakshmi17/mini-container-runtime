"""Internal child process: enter chroot and exec the requested command."""
import ctypes
import os
import sys


def _set_hostname(hostname: str) -> None:
    encoded = hostname.encode()
    if hasattr(os, "sethostname"):
        os.sethostname(encoded)
        return
    # Some CPython builds lack os.sethostname (needs HAVE_SETHOSTNAME at
    # compile time). Fall back to the libc syscall directly; we hold
    # CAP_SYS_ADMIN inside our own UTS namespace here.
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    if libc.sethostname(encoded, len(encoded)) != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, f"sethostname({hostname!r}) failed")


def _mount_proc() -> None:
    """Mount a fresh procfs at /proc inside the new PID namespace.

    This must happen AFTER chroot: mounting before chroot (e.g. via
    unshare --mount-proc) places proc at the host's /proc, which becomes
    unreachable once the root changes. We hold CAP_SYS_ADMIN in our own
    mount namespace here.
    """
    os.makedirs("/proc", exist_ok=True)
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    # mount("proc", "/proc", "proc", 0, NULL)
    if libc.mount(b"proc", b"/proc", b"proc", 0, None) != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, "mount(/proc) failed")


def main() -> int:
    if len(sys.argv) < 5 or sys.argv[3] != "--":
        print("internal usage error", file=sys.stderr)
        return 125
    rootfs, hostname = sys.argv[1], sys.argv[2]
    command = sys.argv[4:]
    try:
        _set_hostname(hostname)
        os.chroot(rootfs)
        os.chdir("/")
        _mount_proc()
        os.execvp(command[0], command)
    except OSError as exc:
        print(f"mini-container child: {exc}", file=sys.stderr)
        return 127
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
