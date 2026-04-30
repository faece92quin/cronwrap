"""Spillover detection: warn when a job runs longer than its scheduled interval."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class SpilloverDetected(Exception):
    """Raised when a job's duration exceeds its scheduled interval."""

    def __init__(self, job: str, duration: float, interval: float) -> None:
        self.job = job
        self.duration = duration
        self.interval = interval
        super().__init__(
            f"Job '{job}' ran for {duration:.1f}s, exceeding its "
            f"{interval:.1f}s interval (overlap: {duration - interval:.1f}s)"
        )


@dataclass
class SpilloverConfig:
    job: str
    interval_seconds: float
    state_dir: str = "/tmp/cronwrap/spillover"
    raise_on_spillover: bool = False
    extra: dict = field(default_factory=dict)


def _state_path(config: SpilloverConfig) -> Path:
    safe = config.job.replace("/", "_").replace(" ", "_")
    return Path(config.state_dir) / f"{safe}.json"


def _load_last_start(config: SpilloverConfig) -> Optional[float]:
    p = _state_path(config)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        return float(data["started_at"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return None


def _save_start(config: SpilloverConfig, started_at: float) -> None:
    p = _state_path(config)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"started_at": started_at, "job": config.job}))


def check_spillover(config: SpilloverConfig, duration: float) -> Optional[SpilloverDetected]:
    """Return a SpilloverDetected instance if duration exceeds interval, else None."""
    if duration > config.interval_seconds:
        exc = SpilloverDetected(config.job, duration, config.interval_seconds)
        if config.raise_on_spillover:
            raise exc
        return exc
    return None


def parse_spillover(
    job: str,
    interval: Optional[str],
    state_dir: str = "/tmp/cronwrap/spillover",
    raise_on_spillover: bool = False,
) -> Optional[SpilloverConfig]:
    """Parse an interval string like '60', '5m', '1h' into a SpilloverConfig."""
    if not interval:
        return None
    interval = interval.strip()
    if not interval:
        return None
    multipliers = {"s": 1, "m": 60, "h": 3600}
    if interval[-1] in multipliers:
        seconds = float(interval[:-1]) * multipliers[interval[-1]]
    else:
        seconds = float(interval)
    return SpilloverConfig(
        job=job,
        interval_seconds=seconds,
        state_dir=state_dir,
        raise_on_spillover=raise_on_spillover,
    )
