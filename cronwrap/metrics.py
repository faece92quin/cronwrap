"""Simple execution metrics collection for cronwrap."""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class ExecutionMetrics:
    command: str
    started_at: float
    finished_at: float
    duration_seconds: float
    exit_code: int
    attempts: int
    succeeded: bool
    stdout_bytes: int = 0
    stderr_bytes: int = 0
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def collect_metrics(
    command: str,
    started_at: float,
    finished_at: float,
    exit_code: int,
    attempts: int,
    stdout: str = "",
    stderr: str = "",
    extra: Optional[dict] = None,
) -> ExecutionMetrics:
    return ExecutionMetrics(
        command=command,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=round(finished_at - started_at, 4),
        exit_code=exit_code,
        attempts=attempts,
        succeeded=exit_code == 0,
        stdout_bytes=len(stdout.encode()),
        stderr_bytes=len(stderr.encode()),
        extra=extra or {},
    )


def write_metrics(metrics: ExecutionMetrics, path: str) -> None:
    """Append a JSON metrics line to *path* (JSONL format)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(metrics.to_json() + "\n")
