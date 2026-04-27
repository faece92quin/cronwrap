"""Schedule drift detection — measures how far a job ran from its intended schedule."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class DriftRecord:
    job_name: str
    scheduled_at: datetime
    actual_at: datetime
    drift_seconds: float

    def exceeded(self, threshold_seconds: float) -> bool:
        return abs(self.drift_seconds) > threshold_seconds


def _drift_path(state_dir: str, job_name: str) -> Path:
    return Path(state_dir) / f"{job_name}.drift.json"


def record_scheduled(state_dir: str, job_name: str, scheduled_at: datetime) -> None:
    """Persist the intended scheduled time before the job runs."""
    path = _drift_path(state_dir, job_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"scheduled_at": scheduled_at.isoformat()}))


def measure_drift(
    state_dir: str,
    job_name: str,
    actual_at: Optional[datetime] = None,
) -> Optional[DriftRecord]:
    """Compute drift between the stored scheduled time and *actual_at* (default: now)."""
    path = _drift_path(state_dir, job_name)
    if not path.exists():
        return None

    data = json.loads(path.read_text())
    scheduled_at = datetime.fromisoformat(data["scheduled_at"])
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

    if actual_at is None:
        actual_at = datetime.now(timezone.utc)
    elif actual_at.tzinfo is None:
        actual_at = actual_at.replace(tzinfo=timezone.utc)

    drift_seconds = (actual_at - scheduled_at).total_seconds()
    return DriftRecord(
        job_name=job_name,
        scheduled_at=scheduled_at,
        actual_at=actual_at,
        drift_seconds=drift_seconds,
    )


def clear_scheduled(state_dir: str, job_name: str) -> bool:
    """Remove the stored scheduled time. Returns True if the file existed."""
    path = _drift_path(state_dir, job_name)
    if path.exists():
        path.unlink()
        return True
    return False


def format_drift(record: DriftRecord) -> str:
    sign = "+" if record.drift_seconds >= 0 else ""
    return (
        f"job={record.job_name} "
        f"scheduled={record.scheduled_at.isoformat()} "
        f"actual={record.actual_at.isoformat()} "
        f"drift={sign}{record.drift_seconds:.1f}s"
    )
