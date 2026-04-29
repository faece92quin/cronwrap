"""CLI sub-commands for inspecting current system pressure."""
from __future__ import annotations

import argparse
import json
import sys

from cronwrap.pressure import (
    PressureConfig,
    PressureExceeded,
    _load_averages,
    _mem_used_pct,
    check_pressure,
)


def build_pressure_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = parent.add_parser("pressure", help="Inspect or enforce resource pressure limits")
    sub = p.add_subparsers(dest="pressure_cmd", required=True)

    show = sub.add_parser("show", help="Print current load and memory usage")
    show.add_argument("--json", dest="as_json", action="store_true")

    chk = sub.add_parser("check", help="Exit non-zero if thresholds are exceeded")
    chk.add_argument("--max-load-1", type=float, default=None)
    chk.add_argument("--max-load-5", type=float, default=None)
    chk.add_argument("--max-mem-pct", type=float, default=None)

    return p


def _cmd_show(args: argparse.Namespace) -> int:
    load1, load5, load15 = _load_averages()
    mem = _mem_used_pct()
    data = {
        "load_1": round(load1, 2),
        "load_5": round(load5, 2),
        "load_15": round(load15, 2),
        "mem_used_pct": round(mem, 1),
    }
    if getattr(args, "as_json", False):
        print(json.dumps(data))
    else:
        print(f"Load avg  : {data['load_1']} (1m)  {data['load_5']} (5m)  {data['load_15']} (15m)")
        print(f"Memory    : {data['mem_used_pct']}% used")
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    cfg = PressureConfig(
        max_load_1=args.max_load_1,
        max_load_5=args.max_load_5,
        max_mem_pct=args.max_mem_pct,
    )
    try:
        check_pressure(cfg)
        print("OK: all pressure checks passed")
        return 0
    except PressureExceeded as exc:
        print(f"EXCEEDED: {exc}", file=sys.stderr)
        return 1


def run_pressure_cli(args: argparse.Namespace) -> int:
    if args.pressure_cmd == "show":
        return _cmd_show(args)
    if args.pressure_cmd == "check":
        return _cmd_check(args)
    return 2
