"""Distributed lease / leader-election primitive backed by a local state file.

A *lease* is a time-bounded ownership token for a named resource.  If the
current process can acquire the lease it holds it for ``ttl`` seconds; any
other process that attempts to acquire the same lease before it expires will
get a ``LeaseHeld`` exception.

This is intentionally file-system based so it works without any external
dependency (Redis, ZooKeeper, …).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class LeaseHeld(Exception:
    """Raised when a lease is already held by another holder."""


@dataclass
class LeaseState:
    holder: str
    acquired_at: float
    ttl: float

    @property
    def expires_at(self) -> float:
        return self.acquired_at + self.ttl

    @property
    def remaining(self) -> float:
        return max(0.0, self.expires_at - time.time())

    @property
    def expired(self) -> bool:
        return time.time() >= self.expires_at


def _lease_path(state_dir: str, name: str) -> Path:
    return Path(state_dir) / f"lease_{name}.json"


def _load_state(path: Path) -> Optional[LeaseState]:
    try:
        data = json.loads(path.read_text())
        return LeaseState(**data)
    except (FileNotFoundError, KeyError, TypeError, json.JSONDecodeError):
        return None


def _save_state(path: Path, state: LeaseState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "holder": state.holder,
        "acquired_at": state.acquired_at,
        "ttl": state.ttl,
    }))


def acquire_lease(name: str, holder: str, ttl: float, state_dir: str) -> LeaseState:
    """Acquire *name* for *holder* for *ttl* seconds.

    Raises ``LeaseHeld`` if the lease is currently held by a different holder
    and has not yet expired.
    """
    path = _lease_path(state_dir, name)
    existing = _load_state(path)
    if existing and not existing.expired and existing.holder != holder:
        raise LeaseHeld(
            f"Lease '{name}' is held by '{existing.holder}' "
            f"for {existing.remaining:.1f}s more."
        )
    state = LeaseState(holder=holder, acquired_at=time.time(), ttl=ttl)
    _save_state(path, state)
    return state


def release_lease(name: str, holder: str, state_dir: str) -> bool:
    """Release *name* if currently held by *holder*.  Returns True on success."""
    path = _lease_path(state_dir, name)
    existing = _load_state(path)
    if existing and existing.holder == holder:
        path.unlink(missing_ok=True)
        return True
    return False


def inspect_lease(name: str, state_dir: str) -> Optional[LeaseState]:
    """Return the current lease state, or None if absent / expired."""
    path = _lease_path(state_dir, name)
    state = _load_state(path)
    if state and state.expired:
        return None
    return state
