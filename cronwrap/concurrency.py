"""Concurrency limit enforcement for cron jobs.

Prevents more than N instances of a named job from running simultaneously
by tracking active PIDs in a state file.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import contextlib


class ConcurrencyLimitExceeded(Exception):
    """Raised when the concurrency limit for a job is reached."""


@dataclass
class ConcurrencyConfig:
    job_name: str
    max_concurrent: int
    state_dir: str = "/tmp/cronwrap/concurrency"


def _state_path(cfg: ConcurrencyConfig) -> Path:
    return Path(cfg.state_dir) / f"{cfg.job_name}.json"


def _load_active(path: Path) -> list[int]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        # Filter to only PIDs that are still alive
        return [pid for pid in data.get("pids", []) if _pid_alive(pid)]
    except (json.JSONDecodeError, KeyError):
        return []


def _save_active(path: Path, pids: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"pids": pids, "updated": time.time()}))


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def check_concurrency(cfg: ConcurrencyConfig) -> list[int]:
    """Check if a new instance can start; raise ConcurrencyLimitExceeded if not."""
    path = _state_path(cfg)
    active = _load_active(path)
    if len(active) >= cfg.max_concurrent:
        raise ConcurrencyLimitExceeded(
            f"Job '{cfg.job_name}' already has {len(active)} active instance(s); "
            f"limit is {cfg.max_concurrent}."
        )
    return active


@contextlib.contextmanager
def concurrency_slot(cfg: ConcurrencyConfig) -> Iterator[None]:
    """Context manager that claims a concurrency slot for the current process."""
    path = _state_path(cfg)
    active = check_concurrency(cfg)
    pid = os.getpid()
    active.append(pid)
    _save_active(path, active)
    try:
        yield
    finally:
        updated = _load_active(path)
        updated = [p for p in updated if p != pid]
        _save_active(path, updated)


def parse_concurrency(value: str | int | None) -> int | None:
    """Parse a concurrency limit value; returns None if not set."""
    if value is None or value == "":
        return None
    try:
        n = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid concurrency limit: {value!r}") from exc
    if n < 1:
        raise ValueError(f"Concurrency limit must be >= 1, got {n}")
    return n
