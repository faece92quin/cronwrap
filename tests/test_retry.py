"""Tests for cronwrap.retry."""

import pytest
from unittest.mock import patch, call
from cronwrap.runner import RunResult
from cronwrap.retry import run_with_retry


def _make_result(exit_code: int, attempt: int = 1) -> RunResult:
    return RunResult(
        command="dummy",
        exit_code=exit_code,
        stdout="",
        stderr="",
        duration_seconds=0.0,
        attempt=attempt,
    )


def test_succeeds_on_first_attempt():
    with patch("cronwrap.retry.run_command", return_value=_make_result(0)) as mock_run:
        result = run_with_retry("echo hi", retries=3, delay=0)
    assert result.success
    mock_run.assert_called_once()


def test_retries_on_failure_then_succeeds():
    side_effects = [_make_result(1, 1), _make_result(1, 2), _make_result(0, 3)]
    with patch("cronwrap.retry.run_command", side_effect=side_effects) as mock_run:
        with patch("cronwrap.retry.time.sleep"):
            result = run_with_retry("flaky", retries=3, delay=0)
    assert result.success
    assert mock_run.call_count == 3


def test_all_attempts_fail():
    side_effects = [_make_result(1, i) for i in range(1, 4)]
    with patch("cronwrap.retry.run_command", side_effect=side_effects):
        with patch("cronwrap.retry.time.sleep"):
            result = run_with_retry("bad", retries=3, delay=0)
    assert not result.success


def test_on_failure_callback_invoked():
    failures = []
    side_effects = [_make_result(1, 1), _make_result(0, 2)]
    with patch("cronwrap.retry.run_command", side_effect=side_effects):
        with patch("cronwrap.retry.time.sleep"):
            run_with_retry("cmd", retries=2, delay=0, on_failure=failures.append)
    assert len(failures) == 1


def test_invalid_retries_raises():
    with pytest.raises(ValueError):
        run_with_retry("cmd", retries=0)
