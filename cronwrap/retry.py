"""Retry logic for failed commands."""

import time
import logging
from typing import Callable, Optional

from cronwrap.runner import RunResult, run_command

logger = logging.getLogger(__name__)


def run_with_retry(
    command: str,
    retries: int = 3,
    delay: float = 5.0,
    timeout: Optional[int] = None,
    on_failure: Optional[Callable[[RunResult], None]] = None,
) -> RunResult:
    """Run a command with retry logic.

    Args:
        command: Shell command to execute.
        retries: Total number of attempts (1 = no retry).
        delay: Seconds to wait between attempts.
        timeout: Per-attempt timeout in seconds.
        on_failure: Optional callback invoked after each failed attempt.

    Returns:
        The last RunResult produced.
    """
    if retries < 1:
        raise ValueError("retries must be >= 1")

    result: RunResult
    for attempt in range(1, retries + 1):
        result = run_command(command, timeout=timeout, attempt=attempt)
        if result.success:
            return result

        if on_failure:
            on_failure(result)

        if attempt < retries:
            logger.info("Retrying in %.1fs… (%d/%d)", delay, attempt, retries)
            time.sleep(delay)
        else:
            logger.error("All %d attempt(s) failed for command: %s", retries, command)

    return result
