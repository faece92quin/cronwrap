"""CLI sub-commands for inspecting execution-window configuration."""

from __future__ import annotations

import argparse
from datetime import datetime
from typing import Optional

from cronwrap.window import WindowConfig, WindowViolation, check_window, parse_window

_DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def build_window_parser(parent: Optional[argparse.ArgumentParser] = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(prog="cronwrap-window")
    sub = parser.add_subparsers(dest="window_cmd")

    check_p = sub.add_parser("check", help="Check whether the current time is inside a window")
    check_p.add_argument("spec", help="Window spec, e.g. '09:00-17:00' or '09:00-17:00/Mon-Fri'")
    check_p.add_argument("--at", metavar="HH:MM", default=None,
                         help="Simulate a specific time (today, HH:MM)")

    show_p = sub.add_parser("show", help="Display parsed window details")
    show_p.add_argument("spec", help="Window spec to display")

    return parser


def _cmd_check(args: argparse.Namespace) -> int:
    try:
        cfg = parse_window(args.spec)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2
    if cfg is None:
        print("No window configured — always allowed.")
        return 0

    now: Optional[datetime] = None
    if args.at:
        try:
            h, m = (int(x) for x in args.at.split(":"))
            now = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        except (ValueError, TypeError):
            print(f"ERROR: invalid --at value {args.at!r}")
            return 2

    try:
        check_window(cfg, now=now)
        print("ALLOWED — current time is inside the window.")
        return 0
    except WindowViolation as exc:
        print(f"BLOCKED — {exc}")
        return 1


def _cmd_show(args: argparse.Namespace) -> int:
    try:
        cfg = parse_window(args.spec)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2
    if cfg is None:
        print("(empty spec)")
        return 0
    days_str = (
        ", ".join(_DAY_NAMES[d] for d in cfg.days) if cfg.days else "every day"
    )
    print(f"Start : {cfg.start.strftime('%H:%M')}")
    print(f"End   : {cfg.end.strftime('%H:%M')}")
    print(f"Days  : {days_str}")
    return 0


def run_window_cli(argv: Optional[list[str]] = None) -> int:
    parser = build_window_parser()
    args = parser.parse_args(argv)
    if args.window_cmd == "check":
        return _cmd_check(args)
    if args.window_cmd == "show":
        return _cmd_show(args)
    parser.print_help()
    return 0
