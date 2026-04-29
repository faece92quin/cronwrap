"""Tests for cronwrap.lock_registry."""

from __future__ import annotations

import os
import time
import pytest

from cronwrap.lock_registry import (
    register_lock,
    unregister_lock,
    list_locks,
    purge_stale_locks,
    LockEntry,
)


@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path / "locks")


def test_register_creates_entry(sdir):
    entry = register_lock("backup", pid=os.getpid(), lock_file="/tmp/backup.lock", state_dir=sdir)
    assert entry.job == "backup"
    assert entry.pid == os.getpid()


def test_list_returns_registered(sdir):
    register_lock("job-a", pid=os.getpid(), lock_file="/tmp/a.lock", state_dir=sdir)
    register_lock("job-b", pid=os.getpid(), lock_file="/tmp/b.lock", state_dir=sdir)
    locks = list_locks(sdir)
    jobs = {l.job for l in locks}
    assert jobs == {"job-a", "job-b"}


def test_register_overwrites_same_job(sdir):
    register_lock("myjob", pid=1111, lock_file="/tmp/x.lock", state_dir=sdir)
    register_lock("myjob", pid=2222, lock_file="/tmp/x.lock", state_dir=sdir)
    locks = list_locks(sdir)
    assert len(locks) == 1
    assert locks[0].pid == 2222


def test_unregister_removes_entry(sdir):
    register_lock("cleanup", pid=os.getpid(), lock_file="/tmp/c.lock", state_dir=sdir)
    removed = unregister_lock("cleanup", state_dir=sdir)
    assert removed is True
    assert list_locks(sdir) == []


def test_unregister_missing_returns_false(sdir):
    assert unregister_lock("ghost", state_dir=sdir) is False


def test_age_seconds_is_nonnegative(sdir):
    entry = register_lock("timer", pid=os.getpid(), lock_file="/tmp/t.lock", state_dir=sdir)
    time.sleep(0.05)
    assert entry.age_seconds() >= 0.04


def test_is_alive_current_process(sdir):
    entry = register_lock("live", pid=os.getpid(), lock_file="/tmp/l.lock", state_dir=sdir)
    assert entry.is_alive() is True


def test_is_alive_dead_pid():
    entry = LockEntry(job="dead", pid=999999999, acquired_at=time.time(), lock_file="/tmp/d.lock")
    assert entry.is_alive() is False


def test_purge_stale_removes_dead_pids(sdir):
    register_lock("alive-job", pid=os.getpid(), lock_file="/tmp/a.lock", state_dir=sdir)
    register_lock("dead-job", pid=999999999, lock_file="/tmp/d.lock", state_dir=sdir)
    purged = purge_stale_locks(state_dir=sdir)
    assert "dead-job" in purged
    assert "alive-job" not in purged
    remaining = {l.job for l in list_locks(sdir)}
    assert remaining == {"alive-job"}


def test_list_empty_when_no_registry(sdir):
    assert list_locks(sdir) == []
