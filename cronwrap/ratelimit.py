"""Rate limiting: prevent a job from running more than N times in a window."""

import json
import os
import time
from pathlib import Path
from typing import Optional


class RateLimitExceeded(Exception):
    """Raised when a job exceeds its allowed run rate."""


def _state_path(state_dir: str, job_name: str) -> Path:
    return Path(state_dir) / f"{job_name}.ratelimit.json"


def _load_timestamps(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_timestamps(path: Path, timestamps: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(timestamps))


def check_rate_limit(
    job_name: str,
    max_runs: int,
    window_seconds: int,
    state_dir: str = "/tmp/cronwrap/ratelimit",
    now: Optional[float] = None,
) -> None:
    """Raise RateLimitExceeded if job has run >= max_runs in the last window_seconds."""
    now = now or time.time()
    path = _state_path(state_dir, job_name)
    timestamps = _load_timestamps(path)
    cutoff = now - window_seconds
    recent = [t for t in timestamps if t >= cutoff]
    if len(recent) >= max_runs:
        raise RateLimitExceeded(
            f"{job_name} has run {len(recent)} times in the last {window_seconds}s "
            f"(max {max_runs})"
        )
    recent.append(now)
    _save_timestamps(path, recent)


def record_run(
    job_name: str,
    window_seconds: int,
    state_dir: str = "/tmp/cronwrap/ratelimit",
    now: Optional[float] = None,
) -> None:
    """Record a run timestamp, pruning entries outside the window."""
    now = now or time.time()
    path = _state_path(state_dir, job_name)
    timestamps = _load_timestamps(path)
    cutoff = now - window_seconds
    timestamps = [t for t in timestamps if t >= cutoff]
    timestamps.append(now)
    _save_timestamps(path, timestamps)
