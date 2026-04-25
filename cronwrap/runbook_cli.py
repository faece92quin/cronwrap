"""CLI sub-commands for managing runbooks."""
from __future__ import annotations

import argparse
import os
import sys

from cronwrap.runbook import Runbook, save_runbook, load_runbook, delete_runbook, list_runbooks

_DEFAULT_DIR = os.path.join(os.path.expanduser("~"), ".cronwrap", "runbooks")


def build_runbook_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    desc = "Manage runbooks attached to cron jobs"
    if parent is not None:
        p = parent.add_parser("runbook", help=desc)
    else:
        p = argparse.ArgumentParser(prog="cronwrap-runbook", description=desc)

    p.add_argument("--state-dir", default=_DEFAULT_DIR, metavar="DIR")
    sub = p.add_subparsers(dest="rb_cmd")

    # set
    s = sub.add_parser("set", help="Attach a runbook to a job")
    s.add_argument("job", help="Job name")
    s.add_argument("--url", default=None)
    s.add_argument("--note", default=None)

    # show
    sh = sub.add_parser("show", help="Show the runbook for a job")
    sh.add_argument("job")

    # delete
    d = sub.add_parser("delete", help="Remove a runbook")
    d.add_argument("job")

    # list
    sub.add_parser("list", help="List all runbooks")

    return p


def run_runbook_cli(args: argparse.Namespace) -> int:
    cmd = args.rb_cmd
    state_dir = args.state_dir

    if cmd == "set":
        rb = Runbook(job_name=args.job, url=args.url, note=args.note)
        save_runbook(rb, state_dir)
        print(f"Runbook saved for '{args.job}'.")
        return 0

    if cmd == "show":
        rb = load_runbook(args.job, state_dir)
        if rb is None:
            print(f"No runbook found for '{args.job}'.")
            return 1
        print(rb.format())
        return 0

    if cmd == "delete":
        removed = delete_runbook(args.job, state_dir)
        if removed:
            print(f"Runbook for '{args.job}' deleted.")
            return 0
        print(f"No runbook found for '{args.job}'.")
        return 1

    if cmd == "list":
        books = list_runbooks(state_dir)
        if not books:
            print("No runbooks stored.")
            return 0
        for rb in books:
            url_part = rb.url or "(no url)"
            print(f"  {rb.job_name:30s}  {url_part}")
        return 0

    print("No sub-command given. Use --help.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    _p = build_runbook_parser()
    _args = _p.parse_args()
    sys.exit(run_runbook_cli(_args))
