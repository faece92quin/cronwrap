"""Tests for cronwrap.circuit_breaker."""
import pytest
import time
from cronwrap.circuit_breaker import (
    CircuitOpen,
    CircuitState,
    check_circuit,
    record_circuit_outcome,
    _state_path,
    _load_state,
)


@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path)


def test_first_run_allowed(sdir):
    state = check_circuit(sdir, "myjob", threshold=3)
    assert state.failures == 0
    assert state.opened_at is None


def test_circuit_opens_after_threshold(sdir):
    now = time.time()
    for _ in range(3):
        record_circuit_outcome(sdir, "myjob", succeeded=False, threshold=3, now=now)
    with pytest.raises(CircuitOpen, match="myjob"):
        check_circuit(sdir, "myjob", threshold=3, now=now + 1)


def test_circuit_stays_open_within_recovery(sdir):
    now = time.time()
    for _ in range(3):
        record_circuit_outcome(sdir, "myjob", succeeded=False, threshold=3, now=now)
    with pytest.raises(CircuitOpen):
        check_circuit(sdir, "myjob", threshold=3, recovery_seconds=300, now=now + 100)


def test_circuit_half_opens_after_recovery(sdir):
    now = time.time()
    for _ in range(3):
        record_circuit_outcome(sdir, "myjob", succeeded=False, threshold=3, now=now)
    # After recovery window, check_circuit should NOT raise
    state = check_circuit(sdir, "myjob", threshold=3, recovery_seconds=60, now=now + 61)
    assert state.opened_at is None
    assert state.failures == 2  # threshold - 1


def test_success_resets_failures(sdir):
    now = time.time()
    for _ in range(2):
        record_circuit_outcome(sdir, "myjob", succeeded=False, threshold=3, now=now)
    record_circuit_outcome(sdir, "myjob", succeeded=True, threshold=3, now=now)
    path = _state_path(sdir, "myjob")
    state = _load_state(path)
    assert state.failures == 0
    assert state.opened_at is None


def test_invalid_threshold_raises(sdir):
    with pytest.raises(ValueError):
        check_circuit(sdir, "myjob", threshold=0)


def test_separate_jobs_independent(sdir):
    now = time.time()
    for _ in range(3):
        record_circuit_outcome(sdir, "job-a", succeeded=False, threshold=3, now=now)
    # job-b should not be affected
    state = check_circuit(sdir, "job-b", threshold=3, now=now + 1)
    assert state.failures == 0


def test_circuit_message_includes_remaining(sdir):
    now = time.time()
    for _ in range(3):
        record_circuit_outcome(sdir, "myjob", succeeded=False, threshold=3, now=now)
    with pytest.raises(CircuitOpen, match=r"\d+s remaining"):
        check_circuit(sdir, "myjob", threshold=3, recovery_seconds=300, now=now + 10)
