"""Simple file-lock based throttle to prevent overlapping cron runs."""
from __future__ import annotations

import fcntl
import logging
import os
from contextlib import contextmanager
from typing import Generator

log = logging.getLogger(__name__)


class AlreadyRunningError(RuntimeError):
    """Raised when a lock file is already held."""


@contextmanager
def exclusive_lock(lock_path: str) -> Generator[None, None, None]:
    """Acquire an exclusive non-blocking lock on *lock_path*.

    Raises AlreadyRunningError if another process holds the lock.
    """
    fd = open(lock_path, "w")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fd.write(str(os.getpid()))
        fd.flush()
        log.debug("Lock acquired: %s", lock_path)
        yield
    except BlockingIOError:
        fd.close()
        raise AlreadyRunningError(
            f"Job is already running (lock held: {lock_path})"
        )
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()
        except Exception:
            pass
