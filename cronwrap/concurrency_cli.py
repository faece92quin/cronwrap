"""CLI sub-commands for inspecting concurrency state."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cronwrap.concurrency import (
    ConcurrencyConfig,
    _load_active,
    _save_active,
    _state_path,
)


def build_concurrency_parser(parent: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = parent.add_parser("concurrency", help="Inspect or reset concurrency state")
    sub = p.add_subparsers(dest="concurrency_cmd", required=True)

    show = sub.add_parser("show", help="Show active PIDs for a job")
    show.add_argument("job", help="Job name")
    show.add_argument("--state-dir", default="/tmp/cronwrap/concurrency")

    reset = sub.add_parser("reset", help="Clear stale concurrency state for a job")
    reset.add_argument("job", help="Job name")
    reset.add_argument("--state-dir", default="/tmp/cronwrap/concurrency")


def _cmd_show(args: argparse.Namespace) -> int:
    cfg = ConcurrencyConfig(job_name=args.job, max_concurrent=1, state_dir=args.state_dir)
    path = _state_path(cfg)
    active = _load_active(path)
    if not active:
        print(f"No active instances for job '{args.job}'.")
    else:
        print(f"Active PIDs for '{args.job}': {active}")
    return 0


def _cmd_reset(args: argparse.Namespace) -> int:
    cfg = ConcurrencyConfig(job_name=args.job, max_concurrent=1, state_dir=args.state_dir)
    path = _state_path(cfg)
    if path.exists():
        _save_active(path, [])
        print(f"Concurrency state reset for job '{args.job}'.")
    else:
        print(f"No concurrency state found for job '{args.job}'.")
    return 0


def run_concurrency_cli(args: argparse.Namespace) -> int:
    if args.concurrency_cmd == "show":
        return _cmd_show(args)
    if args.concurrency_cmd == "reset":
        return _cmd_reset(args)
    return 1
