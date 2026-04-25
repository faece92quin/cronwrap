"""Execution quota enforcement — limit how many times a job may run in a given window."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class QuotaExceeded(Exception):
    """Raised when a job has consumed its allowed executions within the window."""


@dataclass
class QuotaConfig:
    max_runs: int          # maximum executions allowed
    window_seconds: int    # rolling window in seconds
    state_dir: str = "/tmp/cronwrap/quota"


def _quota_path(state_dir: str, job_name: str) -> Path:
    return Path(state_dir) / f"{job_name}.json"


def _load_timestamps(path: Path) -> List[float]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_timestamps(path: Path, timestamps: List[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(timestamps))


def check_quota(config: QuotaConfig, job_name: str, now: Optional[float] = None) -> None:
    """Raise QuotaExceeded if the job has hit its run limit within the window.

    Call this *before* executing the job.  On success the current timestamp is
    appended to the state file so subsequent calls account for this run.
    """
    now = now if now is not None else time.time()
    cutoff = now - config.window_seconds

    path = _quota_path(config.state_dir, job_name)
    timestamps = [t for t in _load_timestamps(path) if t >= cutoff]

    if len(timestamps) >= config.max_runs:
        oldest_next = min(timestamps) + config.window_seconds
        wait = int(oldest_next - now)
        raise QuotaExceeded(
            f"Job '{job_name}' has reached its quota of {config.max_runs} runs "
            f"in {config.window_seconds}s window. Retry in ~{wait}s."
        )

    timestamps.append(now)
    _save_timestamps(path, timestamps)


def parse_quota(max_runs: Optional[int], window: Optional[int], state_dir: str) -> Optional[QuotaConfig]:
    """Return a QuotaConfig or None if either parameter is absent/zero."""
    if not max_runs or not window:
        return None
    return QuotaConfig(max_runs=max_runs, window_seconds=window, state_dir=state_dir)
