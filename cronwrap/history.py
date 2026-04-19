"""Persistent run history for cronwrap jobs."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_DIR = Path.home() / ".cronwrap" / "history"
MAX_ENTRIES = 100


def _history_path(job_name: str, history_dir: Path) -> Path:
    safe = job_name.replace("/", "_").replace(" ", "_")
    return history_dir / f"{safe}.jsonl"


def record_run(
    job_name: str,
    exit_code: int,
    duration: float,
    stdout: str = "",
    stderr: str = "",
    history_dir: Optional[Path] = None,
) -> None:
    """Append a run record to the job's history file."""
    base = Path(history_dir) if history_dir else DEFAULT_HISTORY_DIR
    base.mkdir(parents=True, exist_ok=True)
    path = _history_path(job_name, base)

    entry = {
        "job": job_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "exit_code": exit_code,
        "duration": round(duration, 4),
        "succeeded": exit_code == 0,
        "stdout_bytes": len(stdout.encode()),
        "stderr_bytes": len(stderr.encode()),
    }

    lines: List[str] = []
    if path.exists():
        lines = path.read_text().splitlines()

    lines.append(json.dumps(entry))
    lines = lines[-MAX_ENTRIES:]
    path.write_text("\n".join(lines) + "\n")


def load_history(job_name: str, history_dir: Optional[Path] = None) -> List[dict]:
    """Return list of run records (oldest first) for *job_name*."""
    base = Path(history_dir) if history_dir else DEFAULT_HISTORY_DIR
    path = _history_path(job_name, base)
    if not path.exists():
        return []
    records = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def last_run(job_name: str, history_dir: Optional[Path] = None) -> Optional[dict]:
    """Return the most recent run record or None."""
    history = load_history(job_name, history_dir)
    return history[-1] if history else None
