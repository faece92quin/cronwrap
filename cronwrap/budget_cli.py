"""CLI sub-commands for inspecting and resetting execution time budgets."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwrap.budget import BudgetConfig, _budget_path, _load_durations, _save_durations, average_duration

_DEFAULT_STATE_DIR = "/tmp/cronwrap/budget"


def build_budget_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    if parent is not None:
        p = parent.add_parser("budget", help="Manage execution time budgets")
    else:
        p = argparse.ArgumentParser(prog="cronwrap-budget", description="Manage execution time budgets")

    sub = p.add_subparsers(dest="budget_cmd")

    show = sub.add_parser("show", help="Show recorded durations for a job")
    show.add_argument("job", help="Job name")
    show.add_argument("--state-dir", default=_DEFAULT_STATE_DIR)

    reset = sub.add_parser("reset", help="Clear recorded durations for a job")
    reset.add_argument("job", help="Job name")
    reset.add_argument("--state-dir", default=_DEFAULT_STATE_DIR)

    return p


def _cmd_show(args: argparse.Namespace) -> int:
    cfg = BudgetConfig(job_name=args.job, max_seconds=0, state_dir=args.state_dir)
    durations = _load_durations(cfg)
    if not durations:
        print(f"No duration history for job '{args.job}'.")
        return 0
    avg = average_duration(cfg)
    print(f"Job:      {args.job}")
    print(f"Samples:  {len(durations)}")
    print(f"Average:  {avg:.2f}s")
    print(f"Min:      {min(durations):.2f}s")
    print(f"Max:      {max(durations):.2f}s")
    print(f"Last:     {durations[-1]:.2f}s")
    return 0


def _cmd_reset(args: argparse.Namespace) -> int:
    cfg = BudgetConfig(job_name=args.job, max_seconds=0, state_dir=args.state_dir)
    p = _budget_path(cfg)
    if p.exists():
        p.unlink()
        print(f"Budget history cleared for job '{args.job}'.")
    else:
        print(f"No budget history found for job '{args.job}'.")
    return 0


def run_budget_cli(argv: list[str] | None = None) -> int:
    parser = build_budget_parser()
    args = parser.parse_args(argv)
    if args.budget_cmd == "show":
        return _cmd_show(args)
    if args.budget_cmd == "reset":
        return _cmd_reset(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(run_budget_cli())
