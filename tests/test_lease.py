"""Tests for cronwrap.lease."""

from __future__ import annotations

import time
import pytest

from cronwrap.lease import (
    LeaseHeld,
    LeaseState,
    acquire_lease,
    inspect_lease,
    release_lease,
)


@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# acquire_lease
# ---------------------------------------------------------------------------

def test_acquire_creates_state(sdir):
    state = acquire_lease("job1", "host-a", ttl=60, state_dir=sdir)
    assert isinstance(state, LeaseState)
    assert state.holder == "host-a"
    assert state.ttl == 60
    assert not state.expired


def test_acquire_same_holder_renews(sdir):
    acquire_lease("job1", "host-a", ttl=60, state_dir=sdir)
    state2 = acquire_lease("job1", "host-a", ttl=120, state_dir=sdir)
    assert state2.ttl == 120


def test_acquire_different_holder_raises(sdir):
    acquire_lease("job1", "host-a", ttl=60, state_dir=sdir)
    with pytest.raises(LeaseHeld, match="host-a"):
        acquire_lease("job1", "host-b", ttl=60, state_dir=sdir)


def test_acquire_after_expiry_succeeds(sdir):
    # Use a tiny TTL so it expires immediately.
    acquire_lease("job1", "host-a", ttl=0.01, state_dir=sdir)
    time.sleep(0.05)
    state = acquire_lease("job1", "host-b", ttl=60, state_dir=sdir)
    assert state.holder == "host-b"


# ---------------------------------------------------------------------------
# release_lease
# ---------------------------------------------------------------------------

def test_release_by_owner_returns_true(sdir):
    acquire_lease("job1", "host-a", ttl=60, state_dir=sdir)
    assert release_lease("job1", "host-a", state_dir=sdir) is True


def test_release_by_non_owner_returns_false(sdir):
    acquire_lease("job1", "host-a", ttl=60, state_dir=sdir)
    assert release_lease("job1", "host-b", state_dir=sdir) is False


def test_release_nonexistent_returns_false(sdir):
    assert release_lease("no-such-job", "host-a", state_dir=sdir) is False


def test_release_then_reacquire(sdir):
    acquire_lease("job1", "host-a", ttl=60, state_dir=sdir)
    release_lease("job1", "host-a", state_dir=sdir)
    state = acquire_lease("job1", "host-b", ttl=60, state_dir=sdir)
    assert state.holder == "host-b"


# ---------------------------------------------------------------------------
# inspect_lease
# ---------------------------------------------------------------------------

def test_inspect_returns_state(sdir):
    acquire_lease("job1", "host-a", ttl=60, state_dir=sdir)
    state = inspect_lease("job1", state_dir=sdir)
    assert state is not None
    assert state.holder == "host-a"


def test_inspect_missing_returns_none(sdir):
    assert inspect_lease("ghost", state_dir=sdir) is None


def test_inspect_expired_returns_none(sdir):
    acquire_lease("job1", "host-a", ttl=0.01, state_dir=sdir)
    time.sleep(0.05)
    assert inspect_lease("job1", state_dir=sdir) is None


def test_remaining_decreases_over_time(sdir):
    state = acquire_lease("job1", "host-a", ttl=5, state_dir=sdir)
    r1 = state.remaining
    time.sleep(0.05)
    r2 = state.remaining
    assert r2 < r1
