"""fence_cli.py — CLI sub-commands for inspecting the execution fence."""
from __future__ import annotations

import argparse
from datetime import datetime
from typing import List, Optional

from cronwrap.fence import FenceConfig, FenceViolation, check_fence, parse_fence


def build_fence_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("fence", help="Inspect or test execution fence bounds")
    sub = p.add_subparsers(dest="fence_cmd", required=True)

    # fence check
    chk = sub.add_parser("check", help="Check whether the fence allows running now")
    chk.add_argument("--not-before", metavar="DATE", default=None)
    chk.add_argument("--not-after", metavar="DATE", default=None)
    chk.add_argument(
        "--at",
        metavar="DATETIME",
        default=None,
        help="Override 'now' (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    )

    # fence show
    shw = sub.add_parser("show", help="Display a fence configuration")
    shw.add_argument("--not-before", metavar="DATE", default=None)
    shw.add_argument("--not-after", metavar="DATE", default=None)


def _parse_at(value: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {value!r}")


def run_fence_cli(args: argparse.Namespace) -> int:
    if args.fence_cmd == "show":
        cfg = parse_fence(args.not_before, args.not_after)
        if cfg is None:
            print("No fence configured.")
        else:
            print(f"not_before : {cfg.not_before or '(none)'}")
            print(f"not_after  : {cfg.not_after or '(none)'}")
        return 0

    if args.fence_cmd == "check":
        cfg = parse_fence(args.not_before, args.not_after)
        if cfg is None:
            print("No fence configured — job is always allowed.")
            return 0
        now = _parse_at(args.at) if args.at else None
        try:
            check_fence(cfg, now=now)
            today = (now or datetime.utcnow()).date()
            print(f"ALLOWED — {today} is within the fence.")
            return 0
        except FenceViolation as exc:
            print(f"BLOCKED — {exc}")
            return 1

    return 2
