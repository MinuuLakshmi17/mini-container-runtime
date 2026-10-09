from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .config import load_spec, RunSpec, Limits
from .runner import run, RuntimeErrorMini, build_command


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mini-container", description="Educational Linux namespaces + chroot + cgroups v2 runtime")
    sub = p.add_subparsers(dest="action", required=True)
    v = sub.add_parser("validate", help="validate a JSON run spec")
    v.add_argument("spec")
    d = sub.add_parser("dry-run", help="validate and print the planned command without launching it")
    d.add_argument("spec")
    r = sub.add_parser("run", help="run command inside Linux namespaces and chroot (requires root)")
    r.add_argument("spec")
    r.add_argument("--cgroups", action="store_true", help="apply configured cgroups v2 limits (requires delegation)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        spec = load_spec(args.spec)
        if args.action == "validate":
            print("Spec valid")
            print(json.dumps({"rootfs": str(spec.rootfs), "command": list(spec.command), "hostname": spec.hostname,
                              "limits": spec.limits.__dict__}, indent=2))
            return 0
        return run(spec, dry_run=args.action == "dry-run", use_cgroups=getattr(args, "cgroups", False))
    except (ValueError, KeyError, OSError, RuntimeErrorMini) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
