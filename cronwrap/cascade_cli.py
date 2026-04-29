"""CLI sub-commands for cascade job sequences."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from cronwrap.cascade import (
    CascadeStep,
    format_cascade_result,
    parse_cascade_steps,
    run_cascade,
)
from cronwrap.runner import run_command


def build_cascade_parser(parent: argparse._SubParsersAction = None) -> argparse.ArgumentParser:
    desc = "Run a sequence of dependent commands (cascade)."
    if parent is not None:
        p = parent.add_parser("cascade", help=desc)
    else:
        p = argparse.ArgumentParser(prog="cronwrap cascade", description=desc)

    sub = p.add_subparsers(dest="cascade_cmd")

    run_p = sub.add_parser("run", help="Execute a cascade defined in a JSON file.")
    run_p.add_argument("spec", help="Path to JSON file defining cascade steps.")
    run_p.add_argument(
        "--timeout", default=None, help="Per-step timeout (e.g. 30s, 2m)."
    )
    run_p.add_argument(
        "--quiet", action="store_true", help="Suppress step output."
    )

    show_p = sub.add_parser("show", help="Pretty-print a cascade spec without running it.")
    show_p.add_argument("spec", help="Path to JSON file defining cascade steps.")

    return p


def _load_spec(path: str) -> List[CascadeStep]:
    with open(path) as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("Cascade spec must be a JSON array of step objects.")
    return parse_cascade_steps(data)


def _cmd_run(args: argparse.Namespace) -> int:
    try:
        steps = _load_spec(args.spec)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cascade: error loading spec: {exc}", file=sys.stderr)
        return 2

    def _runner(cmd: str):
        return run_command(cmd, timeout=None)

    def _on_start(step, idx):
        if not args.quiet:
            print(f"[{idx + 1}/{len(steps)}] Running: {step.name}")

    def _on_end(step, result):
        if not args.quiet:
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)

    result = run_cascade(steps, _runner, on_step_start=_on_start, on_step_end=_on_end)
    print(format_cascade_result(result))
    return 0 if result.succeeded else 1


def _cmd_show(args: argparse.Namespace) -> int:
    try:
        steps = _load_spec(args.spec)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cascade: error loading spec: {exc}", file=sys.stderr)
        return 2

    for idx, step in enumerate(steps, 1):
        allow = " (allow_failure)" if step.allow_failure else ""
        print(f"{idx}. {step.name}{allow}")
        print(f"   $ {step.command}")
    return 0


def run_cascade_cli(args: argparse.Namespace) -> int:
    if args.cascade_cmd == "run":
        return _cmd_run(args)
    if args.cascade_cmd == "show":
        return _cmd_show(args)
    print("cascade: specify a sub-command (run, show)", file=sys.stderr)
    return 2
