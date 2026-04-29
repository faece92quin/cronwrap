"""Tests for cronwrap.cascade."""
from __future__ import annotations

import pytest

from cronwrap.cascade import (
    CascadeResult,
    CascadeStep,
    format_cascade_result,
    parse_cascade_steps,
    run_cascade,
)
from cronwrap.runner import RunResult


def _make_result(exit_code: int, stdout: str = "") -> RunResult:
    return RunResult(exit_code=exit_code, stdout=stdout, stderr="", attempt=1)


def _runner_factory(exit_codes):
    codes = iter(exit_codes)

    def _runner(cmd: str) -> RunResult:
        return _make_result(next(codes))

    return _runner


# ---------------------------------------------------------------------------
# parse_cascade_steps
# ---------------------------------------------------------------------------

def test_parse_cascade_steps_minimal():
    raw = [{"name": "build", "command": "make build"}]
    steps = parse_cascade_steps(raw)
    assert len(steps) == 1
    assert steps[0].name == "build"
    assert steps[0].command == "make build"
    assert steps[0].allow_failure is False


def test_parse_cascade_steps_allow_failure():
    raw = [{"name": "lint", "command": "flake8 .", "allow_failure": True}]
    steps = parse_cascade_steps(raw)
    assert steps[0].allow_failure is True


def test_parse_cascade_steps_missing_name_raises():
    with pytest.raises(ValueError, match="name"):
        parse_cascade_steps([{"command": "echo hi"}])


def test_parse_cascade_steps_missing_command_raises():
    with pytest.raises(ValueError, match="command"):
        parse_cascade_steps([{"name": "step1"}])


# ---------------------------------------------------------------------------
# run_cascade
# ---------------------------------------------------------------------------

def test_all_steps_succeed():
    steps = [
        CascadeStep("a", "cmd_a"),
        CascadeStep("b", "cmd_b"),
    ]
    result = run_cascade(steps, _runner_factory([0, 0]))
    assert result.succeeded is True
    assert result.stopped_at is None
    assert result.completed_steps == 2


def test_halts_on_first_failure():
    steps = [
        CascadeStep("a", "cmd_a"),
        CascadeStep("b", "cmd_b"),
        CascadeStep("c", "cmd_c"),
    ]
    result = run_cascade(steps, _runner_factory([0, 1, 0]))
    assert result.succeeded is False
    assert result.stopped_at == "b"
    assert result.completed_steps == 2  # c never ran


def test_allow_failure_continues():
    steps = [
        CascadeStep("a", "cmd_a", allow_failure=True),
        CascadeStep("b", "cmd_b"),
    ]
    result = run_cascade(steps, _runner_factory([1, 0]))
    assert result.succeeded is True
    assert result.completed_steps == 2


def test_callbacks_invoked():
    steps = [CascadeStep("x", "cmd_x")]
    started, ended = [], []
    run_cascade(
        steps,
        _runner_factory([0]),
        on_step_start=lambda s, i: started.append(s.name),
        on_step_end=lambda s, r: ended.append(r.exit_code),
    )
    assert started == ["x"]
    assert ended == [0]


# ---------------------------------------------------------------------------
# format_cascade_result
# ---------------------------------------------------------------------------

def test_format_success_contains_ok():
    steps = [CascadeStep("deploy", "./deploy.sh")]
    result = run_cascade(steps, _runner_factory([0]))
    text = format_cascade_result(result)
    assert "OK" in text
    assert "successfully" in text


def test_format_failure_contains_halted():
    steps = [CascadeStep("test", "pytest"), CascadeStep("deploy", "./deploy.sh")]
    result = run_cascade(steps, _runner_factory([1, 0]))
    text = format_cascade_result(result)
    assert "FAILED" in text
    assert "halted" in text
    assert "test" in text
