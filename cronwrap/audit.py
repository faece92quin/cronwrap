"""Audit trail: record every cronwrap invocation to a append-only JSONL file."""
from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AuditEntry:
    job_name: str
    command: str
    started_at: float
    finished_at: float
    exit_code: int
    attempt: int
    host: str = field(default_factory=socket.gethostname)
    pid: int = field(default_factory=os.getpid)
    tags: dict = field(default_factory=dict)

    @property
    def duration(self) -> float:
        return self.finished_at - self.started_at

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


def _audit_path(audit_dir: str) -> Path:
    p = Path(audit_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p / "audit.jsonl"


def record_audit(entry: AuditEntry, audit_dir: str) -> Path:
    path = _audit_path(audit_dir)
    row = asdict(entry)
    row["duration"] = entry.duration
    row["succeeded"] = entry.succeeded
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    return path


def load_audit(audit_dir: str, job_name: Optional[str] = None) -> list[dict]:
    path = _audit_path(audit_dir)
    if not path.exists():
        return []
    entries = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if job_name is None or row.get("job_name") == job_name:
                entries.append(row)
    return entries


def last_audit(audit_dir: str, job_name: str) -> Optional[dict]:
    entries = load_audit(audit_dir, job_name=job_name)
    return entries[-1] if entries else None
