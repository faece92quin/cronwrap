"""Tests for cronwrap.ratelimit."""

import json
import pytest
from pathlib import Path
from cronwrap.ratelimit import check_rate_limit, record_run, RateLimitExceeded, _state_path


@pytest.fixture
def state_dir(tmp_path):
    return str(tmp_path / "rl")


BASE_TIME = 1_000_000.0


def test_first_run_allowed(state_dir):
    # Should not raise on first run
    check_rate_limit("job", max_runs=3, window_seconds=60, state_dir=state_dir, now=BASE_TIME)


def test_within_limit_allowed(state_dir):
    for i in range(2):
        check_rate_limit("job", max_runs=3, window_seconds=60, state_dir=state_dir, now=BASE_TIME + i)


def test_exceeds_limit_raises(state_dir):
    for i in range(3):
        check_rate_limit("job", max_runs=3, window_seconds=60, state_dir=state_dir, now=BASE_TIME + i)
    with pytest.raises(RateLimitExceeded, match="job"):
        check_rate_limit("job", max_runs=3, window_seconds=60, state_dir=state_dir, now=BASE_TIME + 3)


def test_old_runs_outside_window_not_counted(state_dir):
    # Record 3 runs far in the past
    for i in range(3):
        check_rate_limit("job", max_runs=3, window_seconds=60, state_dir=state_dir, now=BASE_TIME + i)
    # Now run well after the window — should be allowed
    check_rate_limit("job", max_runs=3, window_seconds=60, state_dir=state_dir, now=BASE_TIME + 120)


def test_record_run_prunes_old_entries(state_dir):
    record_run("job", window_seconds=60, state_dir=state_dir, now=BASE_TIME)
    record_run("job", window_seconds=60, state_dir=state_dir, now=BASE_TIME + 200)
    path = _state_path(state_dir, "job")
    timestamps = json.loads(path.read_text())
    assert all(t >= BASE_TIME + 200 - 60 for t in timestamps)


def test_different_jobs_independent(state_dir):
    for i in range(3):
        check_rate_limit("job_a", max_runs=3, window_seconds=60, state_dir=state_dir, now=BASE_TIME + i)
    # job_b should still be allowed
    check_rate_limit("job_b", max_runs=3, window_seconds=60, state_dir=state_dir, now=BASE_TIME)


def test_missing_state_file_treated_as_empty(state_dir):
    # No prior state — should succeed
    check_rate_limit("newjob", max_runs=1, window_seconds=60, state_dir=state_dir, now=BASE_TIME)
