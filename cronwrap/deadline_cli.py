"""CLI sub-commands for inspecting and managing deadline state."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from cronwrap.deadline import (
    DeadlineConfig,
    DeadlineMissed,
    _deadline_path,
    _load_scheduled_time,
    check_deadline,
    record_scheduled_time,
)


def build_deadline_parser(parent: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(prog="cronwrap deadline")
    sub = parser.add_subparsers(dest="deadline_cmd")

    # record
    rec = sub.add_parser("record", help="Record the scheduled time for a job")
    rec.add_argument("job", help="Job name")
    rec.add_argument("--state-dir", default="/var/lib/cronwrap", metavar="DIR")
    rec.add_argument("--at", type=float, default=None, help="Unix timestamp (default: now)")

    # check
    chk = sub.add_parser("check", help="Check whether the job missed its deadline")
    chk.add_argument("job", help="Job name")
    chk.add_argument("--window", required=True, help="Allowed window, e.g. 60 / 2m / 1h")
    chk.add_argument("--state-dir", default="/var/lib/cronwrap", metavar="DIR")

    # show
    shw = sub.add_parser("show", help="Show recorded scheduled time for a job")
    shw.add_argument("job", help="Job name")
    shw.add_argument("--state-dir", default="/var/lib/cronwrap", metavar="DIR")

    # clear
    clr = sub.add_parser("clear", help="Remove deadline state for a job")
    clr.add_argument("job", help="Job name")
    clr.add_argument("--state-dir", default="/var/lib/cronwrap", metavar="DIR")

    return parser


def run_deadline_cli(args: argparse.Namespace) -> int:
    cmd = args.deadline_cmd

    if cmd == "record":
        record_scheduled_time(args.state_dir, args.job, args.at)
        ts = args.at or time.time()
        print(f"Recorded scheduled time {ts:.3f} for job '{args.job}'.")
        return 0

    if cmd == "show":
        ts = _load_scheduled_time(args.state_dir, args.job)
        if ts is None:
            print(f"No deadline state found for job '{args.job}'.")
            return 1
        print(f"Job '{args.job}' scheduled at: {ts:.3f} ({time.ctime(ts)})")
        return 0

    if cmd == "check":
        from cronwrap.deadline import parse_deadline

        window = parse_deadline(args.window)
        cfg = DeadlineConfig(window_seconds=window, job_name=args.job)
        try:
            check_deadline(cfg, args.state_dir)
            print(f"Job '{args.job}' is within its deadline window.")
            return 0
        except DeadlineMissed as exc:
            print(str(exc))
            return 1

    if cmd == "clear":
        path = _deadline_path(args.state_dir, args.job)
        if path.exists():
            path.unlink()
            print(f"Cleared deadline state for job '{args.job}'.")
            return 0
        print(f"No deadline state found for job '{args.job}'.")
        return 1

    print("No sub-command given. Use --help for usage.")
    return 1
