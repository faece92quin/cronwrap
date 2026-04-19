"""Tests for cronwrap.throttle."""
from __future__ import annotations

import os
import tempfile

import pytest

from cronwrap.throttle import AlreadyRunningError, exclusive_lock


def _tmp_lock() -> str:
    fd, path = tempfile.mkstemp(suffix=".lock")
    os.close(fd)
    return path


def test_lock_acquired_and_released():
    path = _tmp_lock()
    with exclusive_lock(path):
        assert os.path.exists(path)
    # After context exits the file still exists but lock is released
    assert os.path.exists(path)
    os.unlink(path)


def test_lock_writes_pid():
    path = _tmp_lock()
    with exclusive_lock(path):
        content = open(path).read()
    assert content == str(os.getpid())
    os.unlink(path)


def test_nested_lock_raises():
    """A second attempt on the same lock file from the same process should fail
    because we request LOCK_NB."""
    path = _tmp_lock()
    with exclusive_lock(path):
        with pytest.raises(AlreadyRunningError):
            with exclusive_lock(path):
                pass
    os.unlink(path)


def test_lock_released_on_exception():
    path = _tmp_lock()
    try:
        with exclusive_lock(path):
            raise ValueError("boom")
    except ValueError:
        pass
    # Should be able to re-acquire after exception
    with exclusive_lock(path):
        pass
    os.unlink(path)
