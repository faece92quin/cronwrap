"""
cronwrap.context
~~~~~~~~~~~~~~~~
ExecutionContext — a single object that travels through the entire cronwrap
pipeline and accumulates everything known about a job run: configuration,
result, metrics, labels, tags, and timing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from cronwrap.labels import Labels


@dataclass
class ExecutionContext:
    """Mutable bag-of-state for a single cron job execution."""

    # --- identity -----------------------------------------------------------
    job_name: str
    command: str
    tags: List[str] = field(default_factory=list)
    labels: Labels = field(default_factory=dict)

    # --- timing -------------------------------------------------------------
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None

    # --- outcome ------------------------------------------------------------
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    attempt: int = 1
    max_attempts: int = 1

    # --- arbitrary extras ---------------------------------------------------
    extra: Dict[str, Any] = field(default_factory=dict)

    # -----------------------------------------------------------------------
    # Derived properties
    # -----------------------------------------------------------------------

    @property
    def succeeded(self) -> Optional[bool]:
        """``True`` if the job exited with code 0, ``None`` if not yet finished."""
        if self.exit_code is None:
            return None
        return self.exit_code == 0

    @property
    def duration_seconds(self) -> Optional[float]:
        """Wall-clock seconds between start and finish, or ``None`` if still running."""
        if self.finished_at is None:
            return None
        return self.finished_at - self.started_at

    @property
    def retried(self) -> bool:
        """``True`` if more than one attempt was made."""
        return self.attempt > 1

    # -----------------------------------------------------------------------
    # Mutators
    # -----------------------------------------------------------------------

    def mark_finished(
        self,
        exit_code: int,
        stdout: str = "",
        stderr: str = "",
        finished_at: Optional[float] = None,
    ) -> None:
        """Record the outcome of the job run."""
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.finished_at = finished_at if finished_at is not None else time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable snapshot of the context."""
        return {
            "job_name": self.job_name,
            "command": self.command,
            "tags": self.tags,
            "labels": self.labels,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds,
            "exit_code": self.exit_code,
            "succeeded": self.succeeded,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "retried": self.retried,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "extra": self.extra,
        }
