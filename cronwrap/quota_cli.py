"""CLI sub-commands for inspecting and resetting job quotas."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from cronwrap.quota import _quota_path, _load_timestamps

_DEFAULT_STATE_DIR = "/tmp/cronwrap/quota"


def build_quota_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = parent.add_parser("quota", help="Inspect or reset job execution quotas")
    sub = p.add_subparsers(dest="quota_cmd", required=True)

    show = sub.add_parser("show", help="Show current quota usage for a job")
    show.add_argument("job", help="Job name")
    show.add_argument("--window", type=int, default=3600, help="Window in seconds (default 3600)")
    show.add_argument("--state-dir", default=_DEFAULT_STATE_DIR)

    reset = sub.add_parser("reset", help="Clear quota history for a job")
    reset.add_argument("job", help="Job name")
    reset.add_argument("--state-dir", default=_DEFAULT_STATE_DIR)

    return p


def _cmd_show(args: argparse.Namespace) -> int:
    path = _quota_path(args.state_dir, args.job)
    now = time.time()
    cutoff = now - args.window
    timestamps = [t for t in _load_timestamps(path) if t >= cutoff]
    print(f"Job      : {args.job}")
    print(f"Window   : {args.window}s")
    print(f"Runs used: {len(timestamps)}")
    if timestamps:
        oldest = min(timestamps)
        resets_in = int(oldest + args.window - now)
        print(f"Resets in: ~{resets_in}s")
    return 0


def _cmd_reset(args: argparse.Namespace) -> int:
    path = _quota_path(args.state_dir, args.job)
    if path.exists():
        path.unlink()
        print(f"Quota history cleared for '{args.job}'.")
    else:
        print(f"No quota history found for '{args.job}'.")
    return 0


def run_quota_cli(args: argparse.Namespace) -> int:
    dispatch = {"show": _cmd_show, "reset": _cmd_reset}
    return dispatch[args.quota_cmd](args)
