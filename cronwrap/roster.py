"""Job roster — tracks registered jobs and their metadata."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class RosterEntry:
    name: str
    command: str
    schedule: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    enabled: bool = True

    def as_dict(self) -> Dict:
        return asdict(self)


def _roster_path(state_dir: str) -> Path:
    return Path(state_dir) / "roster.json"


def _load_roster(state_dir: str) -> Dict[str, RosterEntry]:
    path = _roster_path(state_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        raw: Dict = json.load(fh)
    return {k: RosterEntry(**v) for k, v in raw.items()}


def _save_roster(state_dir: str, roster: Dict[str, RosterEntry]) -> None:
    path = _roster_path(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump({k: v.as_dict() for k, v in roster.items()}, fh, indent=2)


def register_job(state_dir: str, entry: RosterEntry) -> None:
    """Add or update a job in the roster."""
    roster = _load_roster(state_dir)
    roster[entry.name] = entry
    _save_roster(state_dir, roster)


def unregister_job(state_dir: str, name: str) -> bool:
    """Remove a job from the roster. Returns True if it existed."""
    roster = _load_roster(state_dir)
    if name not in roster:
        return False
    del roster[name]
    _save_roster(state_dir, roster)
    return True


def list_jobs(state_dir: str, tag: Optional[str] = None) -> List[RosterEntry]:
    """Return all registered jobs, optionally filtered by tag."""
    roster = _load_roster(state_dir)
    entries = list(roster.values())
    if tag:
        entries = [e for e in entries if tag in e.tags]
    return entries


def get_job(state_dir: str, name: str) -> Optional[RosterEntry]:
    """Return a single job by name, or None."""
    return _load_roster(state_dir).get(name)
