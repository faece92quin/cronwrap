"""CLI sub-commands for the job roster."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from cronwrap.roster import (
    RosterEntry,
    get_job,
    list_jobs,
    register_job,
    unregister_job,
)


def build_roster_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = parent.add_parser("roster", help="Manage the job roster")
    sub = p.add_subparsers(dest="roster_cmd", required=True)

    reg = sub.add_parser("register", help="Register or update a job")
    reg.add_argument("name")
    reg.add_argument("command")
    reg.add_argument("--schedule", default=None)
    reg.add_argument("--tags", nargs="*", default=[])
    reg.add_argument("--description", default=None)
    reg.add_argument("--disabled", action="store_true")
    reg.add_argument("--state-dir", default=".cronwrap")

    rm = sub.add_parser("unregister", help="Remove a job")
    rm.add_argument("name")
    rm.add_argument("--state-dir", default=".cronwrap")

    ls = sub.add_parser("list", help="List registered jobs")
    ls.add_argument("--tag", default=None)
    ls.add_argument("--json", dest="as_json", action="store_true")
    ls.add_argument("--state-dir", default=".cronwrap")

    show = sub.add_parser("show", help="Show a single job")
    show.add_argument("name")
    show.add_argument("--state-dir", default=".cronwrap")

    return p


def run_roster_cli(args: argparse.Namespace) -> int:
    cmd = args.roster_cmd

    if cmd == "register":
        entry = RosterEntry(
            name=args.name,
            command=args.command,
            schedule=args.schedule,
            tags=args.tags or [],
            description=args.description,
            enabled=not args.disabled,
        )
        register_job(args.state_dir, entry)
        print(f"Registered job '{args.name}'.")
        return 0

    if cmd == "unregister":
        removed = unregister_job(args.state_dir, args.name)
        if removed:
            print(f"Unregistered job '{args.name}'.")
            return 0
        print(f"Job '{args.name}' not found.", file=sys.stderr)
        return 1

    if cmd == "list":
        jobs = list_jobs(args.state_dir, tag=args.tag)
        if args.as_json:
            print(json.dumps([j.as_dict() for j in jobs], indent=2))
        else:
            if not jobs:
                print("No jobs registered.")
            for j in jobs:
                status = "enabled" if j.enabled else "disabled"
                tags = ", ".join(j.tags) if j.tags else "-"
                print(f"  {j.name:<20} {status:<10} tags=[{tags}]  {j.command}")
        return 0

    if cmd == "show":
        entry = get_job(args.state_dir, args.name)
        if entry is None:
            print(f"Job '{args.name}' not found.", file=sys.stderr)
            return 1
        print(json.dumps(entry.as_dict(), indent=2))
        return 0

    return 1
