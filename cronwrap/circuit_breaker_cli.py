"""CLI helpers for inspecting circuit breaker state."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from cronwrap.circuit_breaker import _load_state, _state_path


def build_circuit_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-circuit",
        description="Inspect or reset circuit breaker state for a job.",
    )
    parser.add_argument("--state-dir", default="/tmp/cronwrap/circuit", metavar="DIR")
    sub = parser.add_subparsers(dest="cmd")

    show = sub.add_parser("show", help="Show circuit state for a job.")
    show.add_argument("job", help="Job name")

    reset = sub.add_parser("reset", help="Reset circuit breaker for a job.")
    reset.add_argument("job", help="Job name")

    return parser


def _cmd_show(args: argparse.Namespace) -> int:
    path = _state_path(args.state_dir, args.job)
    state = _load_state(path)
    now = time.time()
    status = "closed"
    if state.opened_at is not None:
        status = "open"
    print(json.dumps({
        "job": args.job,
        "status": status,
        "failures": state.failures,
        "opened_at": state.opened_at,
        "last_failure_at": state.last_failure_at,
    }, indent=2))
    return 0


def _cmd_reset(args: argparse.Namespace) -> int:
    path = _state_path(args.state_dir, args.job)
    if path.exists():
        path.unlink()
        print(f"Circuit state reset for '{args.job}'.")
    else:
        print(f"No circuit state found for '{args.job}'.")
    return 0


def run_circuit_cli(argv: list[str] | None = None) -> int:
    parser = build_circuit_parser()
    args = parser.parse_args(argv)
    if args.cmd == "show":
        return _cmd_show(args)
    if args.cmd == "reset":
        return _cmd_reset(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(run_circuit_cli())
