"""Middleware helpers that integrate the roster with the main runner."""
from __future__ import annotations

import argparse
from typing import Optional

from cronwrap.roster import RosterEntry, get_job, register_job


def add_roster_args(parser: argparse.ArgumentParser) -> None:
    """Attach roster-related flags to the main CLI parser."""
    g = parser.add_argument_group("roster")
    g.add_argument(
        "--roster-register",
        action="store_true",
        default=False,
        help="Register/update this job in the roster before running.",
    )
    g.add_argument(
        "--roster-state-dir",
        default=".cronwrap",
        metavar="DIR",
        help="Directory used to persist roster state.",
    )
    g.add_argument(
        "--roster-tags",
        nargs="*",
        default=[],
        metavar="TAG",
        help="Tags to attach when registering this job.",
    )
    g.add_argument(
        "--roster-schedule",
        default=None,
        metavar="CRON",
        help="Cron schedule expression to store with the job.",
    )


def roster_entry_from_args(
    args: argparse.Namespace,
    job_name: str,
    command: str,
) -> Optional[RosterEntry]:
    """Build a RosterEntry from parsed args, or None if registration is off."""
    if not getattr(args, "roster_register", False):
        return None
    return RosterEntry(
        name=job_name,
        command=command,
        schedule=getattr(args, "roster_schedule", None),
        tags=list(getattr(args, "roster_tags", []) or []),
    )


def maybe_register(args: argparse.Namespace, job_name: str, command: str) -> None:
    """Register the job in the roster if --roster-register was passed."""
    entry = roster_entry_from_args(args, job_name, command)
    if entry is not None:
        register_job(getattr(args, "roster_state_dir", ".cronwrap"), entry)


def lookup_command(state_dir: str, name: str) -> Optional[str]:
    """Return the stored command for a job name, or None if not found."""
    entry = get_job(state_dir, name)
    return entry.command if entry else None
