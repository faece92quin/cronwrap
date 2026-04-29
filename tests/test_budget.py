"""Tests for cronwrap.budget and cronwrap.budget_cli."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from cronwrap.budget import (
    BudgetConfig,
    BudgetExceeded,
    _budget_path,
    _load_durations,
    _save_durations,
    average_duration,
    check_budget,
    parse_budget,
    record_duration,
)
from cronwrap.budget_cli import run_budget_cli


@pytest.fixture()
def sdir(tmp_path: Path) -> str:
    return str(tmp_path / "budget")


def _cfg(sdir: str, max_seconds: float = 10.0) -> BudgetConfig:
    return BudgetConfig(job_name="test-job", max_seconds=max_seconds, state_dir=sdir)


# --- parse_budget ---

def test_parse_budget_none_returns_none():
    assert parse_budget("job", None) is None


def test_parse_budget_empty_returns_none():
    assert parse_budget("job", "") is None


def test_parse_budget_plain_int():
    cfg = parse_budget("myjob", "45")
    assert cfg is not None
    assert cfg.max_seconds == 45.0


def test_parse_budget_seconds_suffix():
    cfg = parse_budget("myjob", "30s")
    assert cfg is not None
    assert cfg.max_seconds == 30.0


def test_parse_budget_minutes_suffix():
    cfg = parse_budget("myjob", "2m")
    assert cfg is not None
    assert cfg.max_seconds == 120.0


# --- check_budget ---

def test_check_budget_within_limit_does_not_raise(sdir: str):
    cfg = _cfg(sdir, max_seconds=60.0)
    check_budget(cfg, 30.0)  # should not raise


def test_check_budget_exactly_at_limit_does_not_raise(sdir: str):
    cfg = _cfg(sdir, max_seconds=30.0)
    check_budget(cfg, 30.0)  # boundary: equal is allowed


def test_check_budget_exceeds_raises(sdir: str):
    cfg = _cfg(sdir, max_seconds=10.0)
    with pytest.raises(BudgetExceeded, match="exceeding budget"):
        check_budget(cfg, 15.0)


# --- record_duration / average_duration ---

def test_record_duration_persists(sdir: str):
    cfg = _cfg(sdir)
    record_duration(cfg, 5.0)
    durations = _load_durations(cfg)
    assert durations == [5.0]


def test_record_duration_keeps_last_20(sdir: str):
    cfg = _cfg(sdir)
    for i in range(25):
        record_duration(cfg, float(i))
    durations = _load_durations(cfg)
    assert len(durations) == 20
    assert durations[-1] == 24.0


def test_average_duration_none_when_no_history(sdir: str):
    cfg = _cfg(sdir)
    assert average_duration(cfg) is None


def test_average_duration_computed(sdir: str):
    cfg = _cfg(sdir)
    for v in [10.0, 20.0, 30.0]:
        record_duration(cfg, v)
    assert average_duration(cfg) == pytest.approx(20.0)


# --- CLI ---

def test_cli_show_no_history(sdir: str):
    rc = run_budget_cli(["show", "test-job", "--state-dir", sdir])
    assert rc == 0


def test_cli_show_with_history(sdir: str, capsys: pytest.CaptureFixture):
    cfg = _cfg(sdir)
    for v in [5.0, 10.0, 15.0]:
        record_duration(cfg, v)
    rc = run_budget_cli(["show", "test-job", "--state-dir", sdir])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Samples:  3" in out
    assert "Average:  10.00s" in out


def test_cli_reset_existing(sdir: str, capsys: pytest.CaptureFixture):
    cfg = _cfg(sdir)
    record_duration(cfg, 7.0)
    assert _budget_path(cfg).exists()
    rc = run_budget_cli(["reset", "test-job", "--state-dir", sdir])
    assert rc == 0
    assert not _budget_path(cfg).exists()


def test_cli_reset_nonexistent(sdir: str, capsys: pytest.CaptureFixture):
    rc = run_budget_cli(["reset", "ghost-job", "--state-dir", sdir])
    assert rc == 0
    out = capsys.readouterr().out
    assert "No budget history" in out
