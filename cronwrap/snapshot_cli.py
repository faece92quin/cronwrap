"""CLI sub-commands for inspecting and diffing job snapshots."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from cronwrap.snapshot import load_snapshot
from cronwrap.snapshot_diff import diff_snapshots, format_diff


def build_snapshot_parser(parent: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    sp = parent.add_parser("snapshot", help="Inspect or diff job execution snapshots")
    sub = sp.add_subparsers(dest="snapshot_cmd", required=True)

    show = sub.add_parser("show", help="Print the latest snapshot for a job")
    show.add_argument("job", help="Job name")
    show.add_argument(
        "--dir", default="/var/lib/cronwrap/snapshots", dest="snapshot_dir"
    )
    show.add_argument("--json", action="store_true", dest="as_json")

    diff = sub.add_parser("diff", help="Diff two snapshot files for the same job")
    diff.add_argument("job", help="Job name")
    diff.add_argument("--prev-dir", required=True, dest="prev_dir")
    diff.add_argument("--curr-dir", required=True, dest="curr_dir")


def _cmd_show(args: argparse.Namespace) -> int:
    snap = load_snapshot(args.job, args.snapshot_dir)
    if snap is None:
        print(f"No snapshot found for job '{args.job}' in {args.snapshot_dir}",
              file=sys.stderr)
        return 1
    if args.as_json:
        data = asdict(snap)
        data["duration_seconds"] = snap.duration_seconds
        data["succeeded"] = snap.succeeded
        print(json.dumps(data, indent=2))
    else:
        print(f"Job:      {snap.job_name}")
        print(f"Command:  {snap.command}")
        print(f"Exit:     {snap.exit_code}")
        print(f"Duration: {snap.duration_seconds}s")
        print(f"Attempt:  {snap.attempt}")
        if snap.stdout_preview:
            print(f"Stdout:   {snap.stdout_preview[:120]}")
        if snap.stderr_preview:
            print(f"Stderr:   {snap.stderr_preview[:120]}")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    prev = load_snapshot(args.job, args.prev_dir)
    curr = load_snapshot(args.job, args.curr_dir)
    missing = []
    if prev is None:
        missing.append(f"previous ({args.prev_dir})")
    if curr is None:
        missing.append(f"current ({args.curr_dir})")
    if missing:
        print(f"Snapshot not found: {', '.join(missing)}", file=sys.stderr)
        return 1
    diff = diff_snapshots(prev, curr)  # type: ignore[arg-type]
    print(format_diff(diff))
    return 0


def run_snapshot_cli(args: argparse.Namespace) -> int:
    dispatch = {"show": _cmd_show, "diff": _cmd_diff}
    handler = dispatch.get(args.snapshot_cmd)
    if handler is None:
        print(f"Unknown snapshot sub-command: {args.snapshot_cmd}", file=sys.stderr)
        return 2
    return handler(args)
