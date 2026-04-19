"""Core command runner with logging and exit code handling."""

import subprocess
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    attempt: int = 1
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.exit_code == 0


def run_command(command: str, timeout: Optional[int] = None, attempt: int = 1) -> RunResult:
    """Execute a shell command and return a RunResult."""
    logger.info("Running command (attempt %d): %s", attempt, command)
    start = time.monotonic()

    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = time.monotonic() - start
        result = RunResult(
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_seconds=round(duration, 3),
            attempt=attempt,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - start
        result = RunResult(
            command=command,
            exit_code=1,
            stdout="",
            stderr="",
            duration_seconds=round(duration, 3),
            attempt=attempt,
            error=f"Command timed out after {timeout}s",
        )
        logger.error("Command timed out: %s", exc)

    if result.success:
        logger.info("Command succeeded in %.3fs", result.duration_seconds)
    else:
        logger.warning(
            "Command failed (exit %d) in %.3fs", result.exit_code, result.duration_seconds
        )

    return result
