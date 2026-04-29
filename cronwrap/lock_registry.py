"""Lock registry — tracks and reports on active exclusive locks across jobs."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

_DEFAULT_STATE_DIR = os.path.expanduser("~/.cronwrap/locks")


@dataclass
class LockEntry:
    job: str
    pid: int
    acquired_at: float
    lock_file: str

    def age_seconds(self) -> float:
        return time.time() - self.acquired_at

    def is_alive(self) -> bool:
        """Return True if the process that holds the lock is still running."""
        try:
            os.kill(self.pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False


def _registry_path(state_dir: str) -> Path:
    return Path(state_dir) / "registry.json"


def _load_registry(state_dir: str) -> List[dict]:
    path = _registry_path(state_dir)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_registry(state_dir: str, entries: List[dict]) -> None:
    path = _registry_path(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2))


def register_lock(job: str, pid: int, lock_file: str, state_dir: str = _DEFAULT_STATE_DIR) -> LockEntry:
    """Record that *job* has acquired a lock."""
    entry = LockEntry(job=job, pid=pid, acquired_at=time.time(), lock_file=lock_file)
    entries = _load_registry(state_dir)
    entries = [e for e in entries if e.get("job") != job]
    entries.append(asdict(entry))
    _save_registry(state_dir, entries)
    return entry


def unregister_lock(job: str, state_dir: str = _DEFAULT_STATE_DIR) -> bool:
    """Remove the lock record for *job*. Returns True if a record was removed."""
    entries = _load_registry(state_dir)
    filtered = [e for e in entries if e.get("job") != job]
    if len(filtered) == len(entries):
        return False
    _save_registry(state_dir, filtered)
    return True


def list_locks(state_dir: str = _DEFAULT_STATE_DIR) -> List[LockEntry]:
    """Return all recorded lock entries."""
    return [LockEntry(**e) for e in _load_registry(state_dir)]


def purge_stale_locks(state_dir: str = _DEFAULT_STATE_DIR) -> List[str]:
    """Remove entries whose owning process is no longer alive. Returns purged job names."""
    entries = list_locks(state_dir)
    purged: List[str] = []
    surviving: List[dict] = []
    for entry in entries:
        if entry.is_alive():
            surviving.append(asdict(entry))
        else:
            purged.append(entry.job)
    _save_registry(state_dir, surviving)
    return purged
