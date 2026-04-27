"""Tests for cronwrap.stagger."""
from __future__ import annotations

import pytest

from cronwrap.stagger import (
    StaggerConfig,
    apply_stagger,
    compute_stagger,
    parse_stagger,
)


# ---------------------------------------------------------------------------
# parse_stagger
# ---------------------------------------------------------------------------


def test_parse_stagger_none_returns_none():
    assert parse_stagger(None) is None


def test_parse_stagger_empty_returns_none():
    assert parse_stagger("") is None


def test_parse_stagger_plain_int():
    cfg = parse_stagger("45")
    assert cfg is not None
    assert cfg.max_seconds == 45.0


def test_parse_stagger_seconds_suffix():
    cfg = parse_stagger("30s")
    assert cfg.max_seconds == 30.0


def test_parse_stagger_minutes_suffix():
    cfg = parse_stagger("2m")
    assert cfg.max_seconds == 120.0


def test_parse_stagger_hours_suffix():
    cfg = parse_stagger("1h")
    assert cfg.max_seconds == 3600.0


def test_parse_stagger_decimal():
    cfg = parse_stagger("1.5m")
    assert cfg.max_seconds == pytest.approx(90.0)


def test_parse_stagger_unknown_unit_raises():
    with pytest.raises(ValueError, match="Unknown time unit"):
        parse_stagger("10x")


def test_parse_stagger_bad_format_raises():
    with pytest.raises(ValueError, match="Cannot parse"):
        parse_stagger("abc")


# ---------------------------------------------------------------------------
# compute_stagger
# ---------------------------------------------------------------------------


def test_compute_stagger_within_bounds():
    cfg = StaggerConfig(max_seconds=60.0)
    for _ in range(50):
        delay = compute_stagger(cfg)
        assert 0.0 <= delay <= 60.0


def test_compute_stagger_seeded_is_deterministic():
    cfg = StaggerConfig(max_seconds=100.0, seed=42)
    d1 = compute_stagger(cfg)
    d2 = compute_stagger(cfg)
    assert d1 == d2


def test_compute_stagger_zero_max_returns_zero():
    cfg = StaggerConfig(max_seconds=0.0)
    assert compute_stagger(cfg) == 0.0


# ---------------------------------------------------------------------------
# apply_stagger
# ---------------------------------------------------------------------------


def test_apply_stagger_calls_sleep():
    slept: list[float] = []
    cfg = StaggerConfig(max_seconds=10.0, seed=7)
    result = apply_stagger(cfg, _sleep=slept.append)
    assert len(slept) == 1
    assert slept[0] == pytest.approx(result)
    assert 0.0 <= result <= 10.0


def test_apply_stagger_returns_delay():
    cfg = StaggerConfig(max_seconds=5.0, seed=99)
    delay = apply_stagger(cfg, _sleep=lambda _: None)
    assert 0.0 <= delay <= 5.0
