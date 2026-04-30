"""CLI sub-commands for inspecting spillover state."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cronwrap.spillover import SpilloverConfig, _load_last_start, _state_path


def build_spillover_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = parent.add_parser("spillover", help="Inspect job spillover state")
    sub = p.add_subparsers(dest="spillover_cmd", required=True)

    show = sub.add_parser("show", help="Show last recorded start time for a job")
    show.add_argument("job", help="Job name")
    show.add_argument("--state-dir", default="/tmp/cronwrap/spillover")

    reset = sub.add_parser("reset", help="Clear spillover state for a job")
    reset.add_argument("job", help="Job name")
    reset.add_argument("--state-dir", default="/tmp/cronwrap/spillover")

    return p


def _cmd_show(args: argparse.Namespace) -> int:
    cfg = SpilloverConfig(job=args.job, interval_seconds=0, state_dir=args.state_dir)
    last = _load_last_start(cfg)
    if last is None:
        print(f"No spillover state recorded for job '{args.job}'.")
        return 0
    import datetime
    ts = datetime.datetime.utcfromtimestamp(last).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"Job:         {args.job}")
    print(f"Last start:  {ts} (epoch {last:.3f})")
    return 0


def _cmd_reset(args: argparse.Namespace) -> int:
    cfg = SpilloverConfig(job=args.job, interval_seconds=0, state_dir=args.state_dir)
    p = _state_path(cfg)
    if p.exists():
        p.unlink()
        print(f"Spillover state cleared for job '{args.job}'.")
    else:
        print(f"No spillover state found for job '{args.job}'.")
    return 0


def run_spillover_cli(args: argparse.Namespace) -> int:
    dispatch = {"show": _cmd_show, "reset": _cmd_reset}
    fn = dispatch.get(args.spillover_cmd)
    if fn is None:
        print(f"Unknown spillover command: {args.spillover_cmd}", file=sys.stderr)
        return 2
    return fn(args)
