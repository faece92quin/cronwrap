"""Execution time budget: fail fast if a job consistently exceeds a duration budget."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class BudgetExceeded(Exception):
    """Raised when the job's actual duration exceeds the configured budget."""


@dataclass
class BudgetConfig:
    job_name: str
    max_seconds: float
    state_dir: str = "/tmp/cronwrap/budget"


def _budget_path(cfg: BudgetConfig) -> Path:
    safe = cfg.job_name.replace("/", "_").replace(" ", "_")
    return Path(cfg.state_dir) / f"{safe}.json"


def _load_durations(cfg: BudgetConfig) -> List[float]:
    p = _budget_path(cfg)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_durations(cfg: BudgetConfig, durations: List[float]) -> None:
    p = _budget_path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(durations))


def record_duration(cfg: BudgetConfig, duration: float) -> None:
    """Persist a completed run duration; keep only the last 20 entries."""
    durations = _load_durations(cfg)
    durations.append(duration)
    _save_durations(cfg, durations[-20:])


def check_budget(cfg: BudgetConfig, duration: float) -> None:
    """Raise BudgetExceeded if *duration* exceeds the configured max_seconds."""
    if duration > cfg.max_seconds:
        raise BudgetExceeded(
            f"Job '{cfg.job_name}' ran for {duration:.2f}s, "
            f"exceeding budget of {cfg.max_seconds:.2f}s."
        )


def parse_budget(job_name: str, value: Optional[str], state_dir: str = "/tmp/cronwrap/budget") -> Optional[BudgetConfig]:
    """Parse a budget string like '30', '90s', '5m' into a BudgetConfig."""
    if not value:
        return None
    value = value.strip()
    if value.endswith("m"):
        seconds = float(value[:-1]) * 60
    elif value.endswith("s"):
        seconds = float(value[:-1])
    else:
        seconds = float(value)
    return BudgetConfig(job_name=job_name, max_seconds=seconds, state_dir=state_dir)


def average_duration(cfg: BudgetConfig) -> Optional[float]:
    """Return the average recorded duration, or None if no history exists."""
    durations = _load_durations(cfg)
    if not durations:
        return None
    return sum(durations) / len(durations)
