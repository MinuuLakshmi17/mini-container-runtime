# mini-container-runtime

An educational, deliberately small Linux container runtime in Python. It demonstrates the kernel primitives beneath container tools: namespaces, `chroot`, and cgroups v2. It does **not** aim to be a secure replacement for Docker, LXC/LXD, systemd-nspawn, or a production OCI runtime.

## What it does

- Uses util-linux `unshare` to create mount, UTS, IPC, and PID namespaces.
- Mounts a fresh `/proc` in the PID namespace (`unshare --mount-proc`).
- Sets a private hostname, then enters a supplied root filesystem with `chroot` and `exec`s the command.
- Optionally applies cgroups v2 memory, PID-count, and CPU quota limits.
- Validates a JSON run specification and offers a no-execution `dry-run` mode.
- Has unit tests for configuration validation, namespace command construction, and cgroups file handling.

## Requirements

- Linux, Python 3.10+, and util-linux `unshare`.
- Real execution requires root because this prototype uses `chroot` and `sethostname`. Namespace availability and kernel/container policy can still prevent execution.
- Applying cgroups requires cgroups v2 and a writable/delegated cgroup subtree. Many hosts do not permit direct writes to `/sys/fs/cgroup`.
- The rootfs must contain the executable and its shared libraries. For a shell example, `/bin/sh` and its dynamic dependencies must exist inside the rootfs.

## Install and test

```bash
python -m pip install -e ".[test]"
pytest -q
```

## Try it safely first

Edit `examples/run-spec.json` so `rootfs` points to a prepared Linux root filesystem, then inspect the command without launching it:

```bash
mini-container validate examples/run-spec.json
mini-container dry-run examples/run-spec.json
```

Actual execution (root required):

```bash
sudo mini-container run examples/run-spec.json
```

Apply configured cgroups v2 limits as well (requires delegated writable cgroup hierarchy):

```bash
sudo mini-container run examples/run-spec.json --cgroups
```

## Spec format

The example is JSON to keep the runtime dependency-free. Its structure is YAML-like and could be extended to YAML by adding PyYAML. `rootfs` is an already-built root filesystem; this project does not download or assemble distributions.

- `rootfs`: host path to the root filesystem directory.
- `command`: argv array executed after `chroot`.
- `hostname`: hostname visible in the UTS namespace.
- `limits.memory_max`: bytes, optional.
- `limits.pids_max`: maximum number of tasks, optional.
- `limits.cpu_quota_us` and `limits.cpu_period_us`: cgroups v2 CPU quota parameters, optional.

## Architecture

1. The CLI validates the spec.
2. The parent optionally creates a cgroup and launches `unshare`.
3. `unshare` creates the requested namespaces and mounts `/proc` in the new PID namespace.
4. The child helper sets the hostname, calls `chroot`, changes to `/`, and `exec`s the command.
5. The parent waits for exit and attempts cgroup cleanup.

## Important limitations and security notes

This is a learning prototype, not a security boundary. `chroot` alone is not a complete sandbox. This version does not configure user namespaces/UID mapping, drop capabilities, set `no_new_privs`, apply seccomp or AppArmor/SELinux policy, create a private network namespace, set up device nodes, mount `/dev` or `/sys`, bind-mount selected host directories, or robustly manage process trees during failure. Do not run untrusted workloads or expose this as a service. The cgroup helper assumes its target subtree is already delegated and controllers are available. The prototype uses an existing rootfs and does not fetch base images.

## Next improvements

- User namespace and UID/GID mappings.
- Network namespace and veth setup with explicit opt-in.
- Capability dropping, `no_new_privs`, seccomp, and LSM profiles.
- Robust child supervision and signal forwarding.
- Integration tests in a disposable Linux VM and cgroup delegation tests.
- YAML support and rootfs assembly tooling.

## License

MIT
