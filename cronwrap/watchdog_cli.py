"""CLI sub-commands for inspecting watchdog state."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from cronwrap.watchdog import WatchdogConfig, check_watchdog, record_heartbeat, parse_watchdog


def build_watchdog_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-watchdog",
        description="Inspect or reset cronwrap watchdog state",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    show_p = sub.add_parser("show", help="Show watchdog status for a job")
    show_p.add_argument("job", help="Job name")
    show_p.add_argument("--interval", required=True, help="Expected interval (e.g. 5m, 1h, 300s)")
    show_p.add_argument("--grace", default="60s", help="Grace period (default: 60s)")
    show_p.add_argument("--state-dir", default="/tmp/cronwrap/watchdog")
    show_p.add_argument("--json", dest="as_json", action="store_true")

    touch_p = sub.add_parser("touch", help="Record a heartbeat for a job")
    touch_p.add_argument("job", help="Job name")
    touch_p.add_argument("--interval", required=True)
    touch_p.add_argument("--grace", default="60s")
    touch_p.add_argument("--state-dir", default="/tmp/cronwrap/watchdog")

    return parser


def _cmd_show(args: argparse.Namespace) -> int:
    cfg = parse_watchdog(args.job, args.interval, args.grace, args.state_dir)
    if cfg is None:
        print("ERROR: could not parse interval", file=sys.stderr)
        return 2
    status = check_watchdog(cfg)
    if args.as_json:
        print(json.dumps(status.as_dict(), indent=2))
    else:
        state_str = "OVERDUE" if status.overdue else "OK"
        last = f"{status.last_seen:.0f}" if status.last_seen else "never"
        print(f"job:          {status.job_name}")
        print(f"status:       {state_str}")
        print(f"last_seen:    {last}")
        print(f"interval:     {status.expected_interval_seconds}s")
        print(f"grace:        {status.grace_seconds}s")
        if status.overdue:
            print(f"seconds_overdue: {status.seconds_overdue}")
    return 1 if status.overdue else 0


def _cmd_touch(args: argparse.Namespace) -> int:
    cfg = parse_watchdog(args.job, args.interval, args.grace, args.state_dir)
    if cfg is None:
        print("ERROR: could not parse interval", file=sys.stderr)
        return 2
    record_heartbeat(cfg)
    print(f"Heartbeat recorded for '{args.job}'")
    return 0


def run_watchdog_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_watchdog_parser()
    args = parser.parse_args(argv)
    if args.cmd == "show":
        return _cmd_show(args)
    if args.cmd == "touch":
        return _cmd_touch(args)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run_watchdog_cli())
