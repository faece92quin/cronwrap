"""Timeout utilities for cronwrap."""

import signal
from contextlib import contextmanager
from typing import Optional


class TimeoutExpired(Exception):
    """Raised when an operation exceeds the allowed timeout."""

    def __init__(self, seconds: int):
        self.seconds = seconds
        super().__init__(f"Operation timed out after {seconds}s")


def _handler(signum, frame):
    raise TimeoutExpired(0)  # seconds filled in by context manager


@contextmanager
def time_limit(seconds: Optional[int]):
    """Context manager that raises TimeoutExpired if block exceeds *seconds*.

    Passes through if *seconds* is None or zero (no limit).
    Uses SIGALRM, so only works on Unix.
    """
    if not seconds:
        yield
        return

    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    except TimeoutExpired:
        raise TimeoutExpired(seconds)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def parse_timeout(value: Optional[str]) -> Optional[int]:
    """Parse a timeout string like '30', '2m', '1h' into seconds.

    Returns None if value is None or empty.
    Raises ValueError for unrecognised formats.
    """
    if not value:
        return None
    value = value.strip()
    if value.endswith('h'):
        return int(value[:-1]) * 3600
    if value.endswith('m'):
        return int(value[:-1]) * 60
    if value.endswith('s'):
        return int(value[:-1])
    return int(value)
