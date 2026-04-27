"""Watchdog: detect and record stale/missed job runs based on expected schedule."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class WatchdogConfig:
    job_name: str
    expected_interval_seconds: int
    grace_seconds: int = 60
    state_dir: str = "/tmp/cronwrap/watchdog"


@dataclass
class WatchdogStatus:
    job_name: str
    last_seen: Optional[float]
    expected_interval_seconds: int
    grace_seconds: int
    overdue: bool
    seconds_overdue: float

    def as_dict(self) -> dict:
        return asdict(self)


def _state_path(config: WatchdogConfig) -> Path:
    return Path(config.state_dir) / f"{config.job_name}.json"


def record_heartbeat(config: WatchdogConfig, ts: Optional[float] = None) -> None:
    """Record that the job ran successfully at the given timestamp (default: now)."""
    path = _state_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"job_name": config.job_name, "last_seen": ts if ts is not None else time.time()}
    path.write_text(json.dumps(payload))


def check_watchdog(config: WatchdogConfig, now: Optional[float] = None) -> WatchdogStatus:
    """Return the current watchdog status, indicating whether the job is overdue."""
    if now is None:
        now = time.time()

    path = _state_path(config)
    last_seen: Optional[float] = None

    if path.exists():
        try:
            data = json.loads(path.read_text())
            last_seen = float(data["last_seen"])
        except (KeyError, ValueError, json.JSONDecodeError):
            last_seen = None

    deadline = (last_seen or 0.0) + config.expected_interval_seconds + config.grace_seconds
    overdue = last_seen is None or now > deadline
    seconds_overdue = max(0.0, now - deadline) if overdue else 0.0

    return WatchdogStatus(
        job_name=config.job_name,
        last_seen=last_seen,
        expected_interval_seconds=config.expected_interval_seconds,
        grace_seconds=config.grace_seconds,
        overdue=overdue,
        seconds_overdue=round(seconds_overdue, 2),
    )


def parse_watchdog(job_name: str, interval_arg: Optional[str], grace_arg: Optional[str] = None, state_dir: str = "/tmp/cronwrap/watchdog") -> Optional[WatchdogConfig]:
    """Build a WatchdogConfig from CLI-style string arguments."""
    if not interval_arg:
        return None
    interval_arg = interval_arg.strip()
    if interval_arg.endswith("m"):
        seconds = int(interval_arg[:-1]) * 60
    elif interval_arg.endswith("h"):
        seconds = int(interval_arg[:-1]) * 3600
    elif interval_arg.endswith("s"):
        seconds = int(interval_arg[:-1])
    else:
        seconds = int(interval_arg)
    grace = 60
    if grace_arg:
        grace_arg = grace_arg.strip()
        if grace_arg.endswith("m"):
            grace = int(grace_arg[:-1]) * 60
        elif grace_arg.endswith("s"):
            grace = int(grace_arg[:-1])
        else:
            grace = int(grace_arg)
    return WatchdogConfig(job_name=job_name, expected_interval_seconds=seconds, grace_seconds=grace, state_dir=state_dir)
