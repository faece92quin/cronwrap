"""Checkpoint support: persist and restore named progress markers for long-running jobs."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Checkpoint:
    job: str
    name: str
    value: Any
    saved_at: float = field(default_factory=time.time)

    def age_seconds(self) -> float:
        return time.time() - self.saved_at


def _checkpoint_path(state_dir: str, job: str, name: str) -> Path:
    safe_job = job.replace(os.sep, "_")
    safe_name = name.replace(os.sep, "_")
    return Path(state_dir) / f"{safe_job}.{safe_name}.checkpoint.json"


def save_checkpoint(state_dir: str, job: str, name: str, value: Any) -> Checkpoint:
    """Persist a named checkpoint value to disk."""
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    cp = Checkpoint(job=job, name=name, value=value)
    path = _checkpoint_path(state_dir, job, name)
    path.write_text(json.dumps({"job": cp.job, "name": cp.name, "value": cp.value, "saved_at": cp.saved_at}))
    return cp


def load_checkpoint(state_dir: str, job: str, name: str) -> Optional[Checkpoint]:
    """Load a named checkpoint from disk, or return None if not found."""
    path = _checkpoint_path(state_dir, job, name)
    if not path.exists():
        return None
    data: Dict[str, Any] = json.loads(path.read_text())
    return Checkpoint(
        job=data["job"],
        name=data["name"],
        value=data["value"],
        saved_at=data["saved_at"],
    )


def clear_checkpoint(state_dir: str, job: str, name: str) -> bool:
    """Delete a named checkpoint. Returns True if it existed."""
    path = _checkpoint_path(state_dir, job, name)
    if path.exists():
        path.unlink()
        return True
    return False


def list_checkpoints(state_dir: str, job: str) -> list[str]:
    """Return the names of all saved checkpoints for a job."""
    base = Path(state_dir)
    if not base.exists():
        return []
    prefix = job.replace(os.sep, "_") + "."
    suffix = ".checkpoint.json"
    names = []
    for p in sorted(base.iterdir()):
        fname = p.name
        if fname.startswith(prefix) and fname.endswith(suffix):
            names.append(fname[len(prefix): -len(suffix)])
    return names
