"""Named semaphore for limiting parallel job slots across processes."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator
from contextlib import contextmanager


class SemaphoreExhausted(Exception):
    """Raised when no slots are available on the semaphore."""


@dataclass
class SemaphoreConfig:
    name: str
    slots: int
    state_dir: str = "/tmp/cronwrap/semaphores"


def _state_path(cfg: SemaphoreConfig) -> Path:
    return Path(cfg.state_dir) / f"{cfg.name}.json"


def _load_holders(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_holders(path: Path, holders: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(holders, indent=2))


def _prune_dead(holders: list[dict]) -> list[dict]:
    """Remove entries whose recorded PID is no longer alive."""
    live = []
    for h in holders:
        pid = h.get("pid")
        try:
            os.kill(pid, 0)
            live.append(h)
        except (ProcessLookupError, PermissionError, TypeError):
            pass
    return live


@contextmanager
def semaphore_slot(cfg: SemaphoreConfig) -> Iterator[int]:
    """Acquire one slot on the named semaphore; release on exit.

    Raises SemaphoreExhausted if all slots are occupied by live processes.
    Returns the slot index (0-based) as the context value.
    """
    path = _state_path(cfg)
    holders = _prune_dead(_load_holders(path))

    if len(holders) >= cfg.slots:
        raise SemaphoreExhausted(
            f"Semaphore '{cfg.name}' is full ({cfg.slots}/{cfg.slots} slots in use)"
        )

    entry = {"pid": os.getpid(), "acquired_at": time.time()}
    holders.append(entry)
    _save_holders(path, holders)
    slot_index = len(holders) - 1
    try:
        yield slot_index
    finally:
        current = _prune_dead(_load_holders(path))
        updated = [h for h in current if h.get("pid") != os.getpid()]
        _save_holders(path, updated)


def parse_semaphore(name: str | None, slots_str: str | None, state_dir: str) -> SemaphoreConfig | None:
    """Build a SemaphoreConfig from CLI-style arguments, or None if not configured."""
    if not name or not slots_str:
        return None
    try:
        slots = int(slots_str)
    except (TypeError, ValueError):
        return None
    if slots < 1:
        return None
    return SemaphoreConfig(name=name, slots=slots, state_dir=state_dir)
