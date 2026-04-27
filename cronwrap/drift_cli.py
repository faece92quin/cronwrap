"""CLI sub-commands for inspecting and managing schedule drift records."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from cronwrap.drift import (
    clear_scheduled,
    format_drift,
    measure_drift,
    record_scheduled,
)

_DEFAULT_STATE_DIR = "/var/lib/cronwrap/drift"


def build_drift_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    desc = "Inspect and manage schedule drift records."
    if parent is not None:
        parser = parent.add_parser("drift", help=desc)
    else:
        parser = argparse.ArgumentParser(prog="cronwrap-drift", description=desc)

    parser.add_argument("--state-dir", default=_DEFAULT_STATE_DIR)
    sub = parser.add_subparsers(dest="drift_cmd")

    show_p = sub.add_parser("show", help="Show current drift for a job.")
    show_p.add_argument("job", help="Job name")
    show_p.add_argument("--threshold", type=float, default=0.0,
                        help="Warn if |drift| exceeds this many seconds.")

    record_p = sub.add_parser("record", help="Record the intended scheduled time.")
    record_p.add_argument("job", help="Job name")
    record_p.add_argument("--at", dest="scheduled_at", default=None,
                          help="ISO-8601 scheduled time (default: now).")

    clear_p = sub.add_parser("clear", help="Remove stored scheduled time.")
    clear_p.add_argument("job", help="Job name")

    return parser


def run_drift_cli(args: argparse.Namespace) -> int:
    cmd = getattr(args, "drift_cmd", None)

    if cmd == "show":
        record = measure_drift(args.state_dir, args.job)
        if record is None:
            print(f"No drift record found for job '{args.job}'.")
            return 1
        print(format_drift(record))
        if args.threshold > 0 and record.exceeded(args.threshold):
            print(f"WARNING: drift exceeds threshold of {args.threshold}s", file=sys.stderr)
            return 2
        return 0

    if cmd == "record":
        if args.scheduled_at:
            scheduled_at = datetime.fromisoformat(args.scheduled_at)
        else:
            scheduled_at = datetime.now(timezone.utc)
        record_scheduled(args.state_dir, args.job, scheduled_at)
        print(f"Recorded scheduled time {scheduled_at.isoformat()} for job '{args.job}'.")
        return 0

    if cmd == "clear":
        removed = clear_scheduled(args.state_dir, args.job)
        if removed:
            print(f"Cleared drift record for job '{args.job}'.")
        else:
            print(f"No drift record found for job '{args.job}'.")
        return 0 if removed else 1

    print("No sub-command given. Use show | record | clear.", file=sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    _parser = build_drift_parser()
    sys.exit(run_drift_cli(_parser.parse_args()))
