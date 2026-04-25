"""Runbook attachment — associate a URL or text note with a job for on-call reference."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Runbook:
    job_name: str
    url: Optional[str] = None
    note: Optional[str] = None

    def has_content(self) -> bool:
        return bool(self.url or self.note)

    def format(self) -> str:
        parts = [f"Runbook for job '{self.job_name}':"]
        if self.url:
            parts.append(f"  URL : {self.url}")
        if self.note:
            parts.append(f"  Note: {self.note}")
        if not self.has_content():
            parts.append("  (no runbook configured)")
        return "\n".join(parts)


def _runbook_path(state_dir: str, job_name: str) -> Path:
    return Path(state_dir) / f"{job_name}.runbook.json"


def save_runbook(runbook: Runbook, state_dir: str) -> None:
    path = _runbook_path(state_dir, runbook.job_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(runbook), indent=2))


def load_runbook(job_name: str, state_dir: str) -> Optional[Runbook]:
    path = _runbook_path(state_dir, job_name)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return Runbook(**data)


def delete_runbook(job_name: str, state_dir: str) -> bool:
    path = _runbook_path(state_dir, job_name)
    if path.exists():
        path.unlink()
        return True
    return False


def list_runbooks(state_dir: str) -> list[Runbook]:
    base = Path(state_dir)
    if not base.exists():
        return []
    results = []
    for f in sorted(base.glob("*.runbook.json")):
        try:
            data = json.loads(f.read_text())
            results.append(Runbook(**data))
        except Exception:
            pass
    return results
