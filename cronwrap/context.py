"""Execution context aggregation for cronwrap.

Collects all relevant runtime information into a single context object
that can be passed through the execution pipeline and used by hooks,
alerts, metrics, and reporting.
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ExecutionContext:
    """Holds all metadata and state for a single cron job execution."""

    # Job identity
    job_name: str
    command: str
    tags: List[str] = field(default_factory=list)

    # Runtime environment
    hostname: str = field(default_factory=socket.gethostname)
    username: str = field(default_factory=lambda: os.environ.get("USER", os.environ.get("USERNAME", "unknown")))
    working_dir: str = field(default_factory=os.getcwd)
    pid: int = field(default_factory=os.getpid)

    # Timing
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None

    # Execution outcome
    exit_code: Optional[int] = None
    attempt: int = 1
    max_attempts: int = 1

    # Output
    stdout: str = ""
    stderr: str = ""

    # Arbitrary key/value metadata (e.g. from config extras)
    extra: Dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Derived properties
    # ------------------------------------------------------------------ #

    @property
    def succeeded(self) -> bool:
        """True when the job finished with exit code 0."""
        return self.exit_code == 0

    @property
    def duration_seconds(self) -> Optional[float]:
        """Wall-clock duration in seconds, or None if not yet finished."""
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def retried(self) -> bool:
        """True when more than one attempt was made."""
        return self.attempt > 1

    # ------------------------------------------------------------------ #
    # Mutation helpers
    # ------------------------------------------------------------------ #

    def mark_finished(self, exit_code: int, stdout: str = "", stderr: str = "") -> None:
        """Record the outcome of the command execution."""
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.finished_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict:
        """Serialise the context to a plain dictionary."""
        return {
            "job_name": self.job_name,
            "command": self.command,
            "tags": self.tags,
            "hostname": self.hostname,
            "username": self.username,
            "working_dir": self.working_dir,
            "pid": self.pid,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_seconds": self.duration_seconds,
            "exit_code": self.exit_code,
            "succeeded": self.succeeded,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "retried": self.retried,
            "extra": self.extra,
        }


def build_context(
    job_name: str,
    command: str,
    *,
    tags: Optional[List[str]] = None,
    max_attempts: int = 1,
    extra: Optional[Dict[str, str]] = None,
) -> ExecutionContext:
    """Factory that creates an :class:`ExecutionContext` with sensible defaults.

    Parameters
    ----------
    job_name:
        Human-readable identifier for the cron job.
    command:
        The shell command that will be executed.
    tags:
        Optional list of tag strings for filtering/grouping.
    max_attempts:
        Total number of attempts allowed (including the first).
    extra:
        Arbitrary key/value pairs to attach to the context.
    """
    return ExecutionContext(
        job_name=job_name,
        command=command,
        tags=list(tags) if tags else [],
        max_attempts=max(1, max_attempts),
        extra=dict(extra) if extra else {},
    )
