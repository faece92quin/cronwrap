"""Tests for cronwrap.window."""

from __future__ import annotations

from datetime import datetime, time

import pytest

from cronwrap.window import (
    WindowConfig,
    WindowViolation,
    check_window,
    parse_window,
)


# ---------------------------------------------------------------------------
# parse_window
# ---------------------------------------------------------------------------

def test_parse_window_none_returns_none():
    assert parse_window(None) is None


def test_parse_window_empty_returns_none():
    assert parse_window("") is None


def test_parse_window_basic():
    cfg = parse_window("09:00-17:00")
    assert cfg is not None
    assert cfg.start == time(9, 0)
    assert cfg.end == time(17, 0)
    assert cfg.days is None


def test_parse_window_with_days():
    cfg = parse_window("08:00-18:00/Mon,Wed,Fri")
    assert cfg is not None
    assert cfg.days == [0, 2, 4]


def test_parse_window_invalid_time_raises():
    with pytest.raises(ValueError, match="Invalid time format"):
        parse_window("9am-5pm")


def test_parse_window_invalid_day_raises():
    with pytest.raises(ValueError, match="Unknown day"):
        parse_window("09:00-17:00/Mon,Xyz")


def test_parse_window_missing_dash_raises():
    with pytest.raises(ValueError, match="must contain"):
        parse_window("0900")


# ---------------------------------------------------------------------------
# check_window
# ---------------------------------------------------------------------------

def _at(h: int, m: int, weekday: int = 0) -> datetime:
    """Build a datetime with the given hour/minute on the given weekday."""
    # Find a Monday in the future as base (weekday 0)
    base = datetime(2024, 1, 1)  # 2024-01-01 is a Monday
    from datetime import timedelta
    return base + timedelta(days=weekday, hours=h, minutes=m)


def test_check_window_inside_allowed():
    cfg = WindowConfig(start=time(9, 0), end=time(17, 0))
    check_window(cfg, now=_at(12, 0))  # should not raise


def test_check_window_exactly_on_start():
    cfg = WindowConfig(start=time(9, 0), end=time(17, 0))
    check_window(cfg, now=_at(9, 0))


def test_check_window_exactly_on_end():
    cfg = WindowConfig(start=time(9, 0), end=time(17, 0))
    check_window(cfg, now=_at(17, 0))


def test_check_window_before_start_raises():
    cfg = WindowConfig(start=time(9, 0), end=time(17, 0))
    with pytest.raises(WindowViolation, match="outside allowed window"):
        check_window(cfg, now=_at(8, 59))


def test_check_window_after_end_raises():
    cfg = WindowConfig(start=time(9, 0), end=time(17, 0))
    with pytest.raises(WindowViolation, match="outside allowed window"):
        check_window(cfg, now=_at(17, 1))


def test_check_window_wrong_day_raises():
    cfg = WindowConfig(start=time(9, 0), end=time(17, 0), days=[0, 1, 2, 3, 4])
    saturday = _at(12, 0, weekday=5)
    with pytest.raises(WindowViolation, match="not allowed on"):
        check_window(cfg, now=saturday)


def test_check_window_correct_day_passes():
    cfg = WindowConfig(start=time(9, 0), end=time(17, 0), days=[0, 1, 2, 3, 4])
    monday = _at(12, 0, weekday=0)
    check_window(cfg, now=monday)  # should not raise
