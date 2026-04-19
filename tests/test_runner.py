"""Tests for cronwrap.runner."""

import pytest
from cronwrap.runner import run_command, RunResult


def test_successful_command():
    result = run_command("echo hello")
    assert result.success
    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert result.duration_seconds >= 0
    assert result.error is None


def test_failed_command():
    result = run_command("exit 1")
    assert not result.success
    assert result.exit_code == 1


def test_stderr_captured():
    result = run_command("echo err >&2")
    assert "err" in result.stderr


def test_timeout_returns_failure():
    result = run_command("sleep 10", timeout=1)
    assert not result.success
    assert result.error is not None
    assert "timed out" in result.error.lower()


def test_attempt_stored():
    result = run_command("true", attempt=3)
    assert result.attempt == 3


def test_run_result_repr():
    r = RunResult(command="ls", exit_code=0, stdout="", stderr="", duration_seconds=0.1)
    assert r.success is True
