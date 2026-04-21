"""Execution snapshot: capture and persist a point-in-time view of a job run."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Snapshot:
    job_name: str
    command: str
    started_at: float
    finished_at: Optional[float]
    exit_code: Optional[int]
    stdout_preview: str
    stderr_preview: str
    attempt: int
    tags: list
    labels: dict

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.finished_at is None:
            return None
        return round(self.finished_at - self.started_at, 3)

    @property
    def succeeded(self) -> Optional[bool]:
        if self.exit_code is None:
            return None
        return self.exit_code == 0


def _snapshot_path(base_dir: str, job_name: str) -> Path:
    safe = job_name.replace(os.sep, "_").replace(" ", "_")
    return Path(base_dir) / f"{safe}.snapshot.json"


def save_snapshot(snapshot: Snapshot, base_dir: str) -> Path:
    path = _snapshot_path(base_dir, snapshot.job_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(snapshot)
    data["duration_seconds"] = snapshot.duration_seconds
    data["succeeded"] = snapshot.succeeded
    path.write_text(json.dumps(data, indent=2))
    return path


def load_snapshot(job_name: str, base_dir: str) -> Optional[Snapshot]:
    path = _snapshot_path(base_dir, job_name)
    if not path.exists():
        return None
    raw = json.loads(path.read_text())
    raw.pop("duration_seconds", None)
    raw.pop("succeeded", None)
    return Snapshot(**raw)


def build_snapshot(
    job_name: str,
    command: str,
    started_at: float,
    finished_at: Optional[float],
    exit_code: Optional[int],
    stdout: str,
    stderr: str,
    attempt: int = 1,
    tags: Optional[list] = None,
    labels: Optional[dict] = None,
    preview_chars: int = 500,
) -> Snapshot:
    return Snapshot(
        job_name=job_name,
        command=command,
        started_at=started_at,
        finished_at=finished_at,
        exit_code=exit_code,
        stdout_preview=stdout[:preview_chars],
        stderr_preview=stderr[:preview_chars],
        attempt=attempt,
        tags=tags or [],
        labels=labels or {},
    )
