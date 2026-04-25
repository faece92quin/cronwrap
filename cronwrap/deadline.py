"""Deadline enforcement: skip a job if it missed its execution window."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class DeadlineMissed(Exception):
    """Raised when a job is started after its allowed deadline window."""


@dataclass
class DeadlineConfig:
    """Configuration for deadline enforcement."""

    window_seconds: int  # how many seconds after scheduled time the job may still start
    job_name: str


def _deadline_path(state_dir: str, job_name: str) -> Path:
    return Path(state_dir) / f"{job_name}.deadline.json"


def record_scheduled_time(
    state_dir: str, job_name: str, scheduled_at: Optional[float] = None
) -> None:
    """Persist the time at which this job was *scheduled* to run."""
    path = _deadline_path(state_dir, job_name)
    os.makedirs(state_dir, exist_ok=True)
    payload = {"scheduled_at": scheduled_at if scheduled_at is not None else time.time()}
    path.write_text(json.dumps(payload))


def _load_scheduled_time(state_dir: str, job_name: str) -> Optional[float]:
    path = _deadline_path(state_dir, job_name)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return float(data["scheduled_at"])


def check_deadline(
    cfg: DeadlineConfig,
    state_dir: str,
    now: Optional[float] = None,
) -> None:
    """Raise DeadlineMissed if the job started too late.

    If no scheduled time has been recorded the check is skipped (first run).
    """
    scheduled_at = _load_scheduled_time(state_dir, cfg.job_name)
    if scheduled_at is None:
        return

    current = now if now is not None else time.time()
    elapsed = current - scheduled_at
    if elapsed > cfg.window_seconds:
        raise DeadlineMissed(
            f"Job '{cfg.job_name}' missed its deadline: started {elapsed:.1f}s after "
            f"scheduled time (window={cfg.window_seconds}s)."
        )


def parse_deadline(window: Optional[str]) -> Optional[int]:
    """Parse a deadline window string such as '30', '2m', '1h' into seconds."""
    if not window:
        return None
    window = window.strip()
    if window.endswith("h"):
        return int(window[:-1]) * 3600
    if window.endswith("m"):
        return int(window[:-1]) * 60
    if window.endswith("s"):
        return int(window[:-1])
    return int(window)
