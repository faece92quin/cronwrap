"""Execution window enforcement — restrict jobs to allowed time windows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional


class WindowViolation(Exception):
    """Raised when a job is invoked outside its allowed execution window."""


@dataclass
class WindowConfig:
    start: time  # inclusive
    end: time    # inclusive
    days: Optional[list[int]] = None  # 0=Mon … 6=Sun; None means every day
    timezone: str = "local"


def _parse_time(value: str) -> time:
    """Parse HH:MM (24-hour) into a time object."""
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", value.strip())
    if not m:
        raise ValueError(f"Invalid time format {value!r}; expected HH:MM")
    hour, minute = int(m.group(1)), int(m.group(2))
    return time(hour, minute)


def parse_window(spec: Optional[str]) -> Optional[WindowConfig]:
    """Parse a window spec string like '09:00-17:00' or '09:00-17:00/Mon-Fri'.

    Returns None when *spec* is None or empty.
    """
    if not spec:
        return None
    parts = spec.strip().split("/")
    time_part = parts[0]
    days_part = parts[1] if len(parts) > 1 else None

    if "-" not in time_part:
        raise ValueError(f"Window spec must contain '-': {spec!r}")
    start_str, end_str = time_part.split("-", 1)
    start = _parse_time(start_str)
    end = _parse_time(end_str)

    days: Optional[list[int]] = None
    if days_part:
        day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        days = []
        for d in days_part.split(","):
            key = d.strip().lower()[:3]
            if key not in day_map:
                raise ValueError(f"Unknown day {d!r} in window spec")
            days.append(day_map[key])

    return WindowConfig(start=start, end=end, days=days)


def check_window(cfg: WindowConfig, now: Optional[datetime] = None) -> None:
    """Raise WindowViolation if *now* falls outside the configured window."""
    if now is None:
        now = datetime.now()

    current_time = now.time().replace(second=0, microsecond=0)
    current_day = now.weekday()

    if cfg.days is not None and current_day not in cfg.days:
        raise WindowViolation(
            f"Job not allowed on {now.strftime('%A')}; "
            f"permitted days: {cfg.days}"
        )

    if not (cfg.start <= current_time <= cfg.end):
        raise WindowViolation(
            f"Current time {current_time.strftime('%H:%M')} is outside "
            f"allowed window {cfg.start.strftime('%H:%M')}-{cfg.end.strftime('%H:%M')}"
        )
