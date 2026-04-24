"""CLI sub-commands for inspecting and managing job checkpoints."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from cronwrap.checkpoint import clear_checkpoint, list_checkpoints, load_checkpoint


def build_checkpoint_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("checkpoint", help="Manage job checkpoints")
    sub = p.add_subparsers(dest="cp_cmd", required=True)

    ls = sub.add_parser("list", help="List checkpoints for a job")
    ls.add_argument("job", help="Job name")
    ls.add_argument("--state-dir", default=".cronwrap/checkpoints", metavar="DIR")

    show = sub.add_parser("show", help="Show a specific checkpoint value")
    show.add_argument("job", help="Job name")
    show.add_argument("name", help="Checkpoint name")
    show.add_argument("--state-dir", default=".cronwrap/checkpoints", metavar="DIR")

    rm = sub.add_parser("clear", help="Delete a checkpoint")
    rm.add_argument("job", help="Job name")
    rm.add_argument("name", help="Checkpoint name")
    rm.add_argument("--state-dir", default=".cronwrap/checkpoints", metavar="DIR")


def _cmd_list(args: argparse.Namespace) -> int:
    names = list_checkpoints(args.state_dir, args.job)
    if not names:
        print(f"No checkpoints found for job '{args.job}'.")
        return 0
    for name in names:
        print(name)
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    cp = load_checkpoint(args.state_dir, args.job, args.name)
    if cp is None:
        print(f"Checkpoint '{args.name}' not found for job '{args.job}'.", file=sys.stderr)
        return 1
    print(json.dumps({"job": cp.job, "name": cp.name, "value": cp.value, "age_seconds": round(cp.age_seconds(), 3)}, indent=2))
    return 0


def _cmd_clear(args: argparse.Namespace) -> int:
    removed = clear_checkpoint(args.state_dir, args.job, args.name)
    if removed:
        print(f"Cleared checkpoint '{args.name}' for job '{args.job}'.")
        return 0
    print(f"Checkpoint '{args.name}' not found for job '{args.job}'.", file=sys.stderr)
    return 1


def run_checkpoint_cli(args: argparse.Namespace) -> int:
    dispatch = {"list": _cmd_list, "show": _cmd_show, "clear": _cmd_clear}
    handler = dispatch.get(args.cp_cmd)
    if handler is None:
        print(f"Unknown sub-command: {args.cp_cmd}", file=sys.stderr)
        return 2
    return handler(args)
