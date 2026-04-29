"""Tests for cronwrap.cooldown."""

import pytest
from cronwrap.cooldown import check_cooldown, reset_cooldown, CooldownActive


BASE = 1_000_000.0


@pytest.fixture
def sdir(tmp_path):
    return str(tmp_path / "cd")


def test_first_run_always_allowed(sdir):
    check_cooldown("job", cooldown_seconds=30, state_dir=sdir, now=BASE)


def test_run_after_cooldown_allowed(sdir):
    check_cooldown("job", cooldown_seconds=30, state_dir=sdir, now=BASE)
    check_cooldown("job", cooldown_seconds=30, state_dir=sdir, now=BASE + 31)


def test_run_during_cooldown_raises(sdir):
    check_cooldown("job", cooldown_seconds=30, state_dir=sdir, now=BASE)
    with pytest.raises(CooldownActive, match="job"):
        check_cooldown("job", cooldown_seconds=30, state_dir=sdir, now=BASE + 10)


def test_cooldown_message_includes_remaining(sdir):
    check_cooldown("job", cooldown_seconds=60, state_dir=sdir, now=BASE)
    with pytest.raises(CooldownActive, match="50.0s more"):
        check_cooldown("job", cooldown_seconds=60, state_dir=sdir, now=BASE + 10)


def test_reset_allows_immediate_rerun(sdir):
    check_cooldown("job", cooldown_seconds=60, state_dir=sdir, now=BASE)
    reset_cooldown("job", state_dir=sdir)
    check_cooldown("job", cooldown_seconds=60, state_dir=sdir, now=BASE + 1)


def test_reset_nonexistent_is_safe(sdir):
    reset_cooldown("ghost", state_dir=sdir)  # should not raise


def test_different_jobs_independent(sdir):
    check_cooldown("job_a", cooldown_seconds=60, state_dir=sdir, now=BASE)
    # job_b has no cooldown yet
    check_cooldown("job_b", cooldown_seconds=60, state_dir=sdir, now=BASE + 5)


def test_run_exactly_at_cooldown_boundary_allowed(sdir):
    """A run at exactly cooldown_seconds after the last run should be permitted."""
    check_cooldown("job", cooldown_seconds=30, state_dir=sdir, now=BASE)
    check_cooldown("job", cooldown_seconds=30, state_dir=sdir, now=BASE + 30)
