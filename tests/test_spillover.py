"""Tests for cronwrap.spillover."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from cronwrap.spillover import (
    SpilloverConfig,
    SpilloverDetected,
    _load_last_start,
    _save_start,
    _state_path,
    check_spillover,
    parse_spillover,
)


@pytest.fixture()
def sdir(tmp_path: Path) -> str:
    return str(tmp_path / "spillover")


def _cfg(job: str, interval: float, sdir: str, raise_on: bool = False) -> SpilloverConfig:
    return SpilloverConfig(job=job, interval_seconds=interval, state_dir=sdir, raise_on_spillover=raise_on)


# --- parse_spillover ---

def test_parse_spillover_none_returns_none():
    assert parse_spillover("myjob", None) is None


def test_parse_spillover_empty_returns_none():
    assert parse_spillover("myjob", "") is None


def test_parse_spillover_plain_int():
    cfg = parse_spillover("myjob", "120")
    assert cfg is not None
    assert cfg.interval_seconds == 120.0


def test_parse_spillover_seconds_suffix():
    cfg = parse_spillover("myjob", "45s")
    assert cfg.interval_seconds == 45.0


def test_parse_spillover_minutes_suffix():
    cfg = parse_spillover("myjob", "5m")
    assert cfg.interval_seconds == 300.0


def test_parse_spillover_hours_suffix():
    cfg = parse_spillover("myjob", "2h")
    assert cfg.interval_seconds == 7200.0


# --- check_spillover ---

def test_no_spillover_returns_none(sdir):
    cfg = _cfg("job1", 60.0, sdir)
    result = check_spillover(cfg, 30.0)
    assert result is None


def test_exact_interval_no_spillover(sdir):
    cfg = _cfg("job1", 60.0, sdir)
    result = check_spillover(cfg, 60.0)
    assert result is None


def test_spillover_returns_exception_object(sdir):
    cfg = _cfg("job1", 60.0, sdir)
    result = check_spillover(cfg, 75.0)
    assert isinstance(result, SpilloverDetected)
    assert result.duration == 75.0
    assert result.interval == 60.0
    assert result.job == "job1"


def test_spillover_message_contains_overlap(sdir):
    cfg = _cfg("job1", 60.0, sdir)
    exc = check_spillover(cfg, 75.0)
    assert "15.0s" in str(exc)


def test_spillover_raises_when_configured(sdir):
    cfg = _cfg("job1", 60.0, sdir, raise_on=True)
    with pytest.raises(SpilloverDetected):
        check_spillover(cfg, 90.0)


# --- state persistence ---

def test_save_and_load_last_start(sdir):
    cfg = _cfg("backup", 3600.0, sdir)
    now = time.time()
    _save_start(cfg, now)
    loaded = _load_last_start(cfg)
    assert loaded is not None
    assert abs(loaded - now) < 0.001


def test_load_missing_returns_none(sdir):
    cfg = _cfg("nonexistent", 60.0, sdir)
    assert _load_last_start(cfg) is None


def test_state_path_sanitizes_slashes(sdir):
    cfg = _cfg("org/team/job", 60.0, sdir)
    p = _state_path(cfg)
    assert "/" not in p.name
