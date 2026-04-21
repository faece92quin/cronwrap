"""Tests for cronwrap.jitter."""

from __future__ import annotations

import random

import pytest

from cronwrap.jitter import JitterConfig, apply_jitter, parse_jitter


# ---------------------------------------------------------------------------
# JitterConfig validation
# ---------------------------------------------------------------------------

def test_invalid_strategy_raises():
    with pytest.raises(ValueError, match="Unknown jitter strategy"):
        JitterConfig(strategy="random_walk")  # type: ignore[arg-type]


def test_zero_max_delay_raises():
    with pytest.raises(ValueError, match="max_delay must be positive"):
        JitterConfig(max_delay=0)


def test_negative_max_delay_raises():
    with pytest.raises(ValueError, match="max_delay must be positive"):
        JitterConfig(max_delay=-5.0)


# ---------------------------------------------------------------------------
# Strategy: none
# ---------------------------------------------------------------------------

def test_none_strategy_returns_delay_unchanged():
    cfg = JitterConfig(strategy="none", max_delay=120.0)
    assert apply_jitter(10.0, cfg) == 10.0


def test_none_strategy_respects_max_delay():
    cfg = JitterConfig(strategy="none", max_delay=5.0)
    assert apply_jitter(100.0, cfg) == 5.0


# ---------------------------------------------------------------------------
# Strategy: full
# ---------------------------------------------------------------------------

def test_full_jitter_within_range():
    cfg = JitterConfig(strategy="full", max_delay=60.0)
    rng = random.Random(42)
    for _ in range(50):
        result = apply_jitter(20.0, cfg, rng=rng)
        assert 0.0 <= result <= 20.0


def test_full_jitter_capped_at_max_delay():
    cfg = JitterConfig(strategy="full", max_delay=5.0)
    rng = random.Random(0)
    result = apply_jitter(100.0, cfg, rng=rng)
    assert result <= 5.0


# ---------------------------------------------------------------------------
# Strategy: half
# ---------------------------------------------------------------------------

def test_half_jitter_lower_bound():
    cfg = JitterConfig(strategy="half", max_delay=60.0)
    rng = random.Random(7)
    for _ in range(50):
        result = apply_jitter(20.0, cfg, rng=rng)
        assert result >= 10.0
        assert result <= 20.0


# ---------------------------------------------------------------------------
# Strategy: decorrelated
# ---------------------------------------------------------------------------

def test_decorrelated_uses_prev_delay():
    cfg = JitterConfig(strategy="decorrelated", max_delay=300.0)
    rng = random.Random(99)
    # With a large prev_delay the upper bound should grow
    result = apply_jitter(1.0, cfg, prev_delay=30.0, rng=rng)
    assert result >= 1.0
    assert result <= 90.0  # upper = max(1, 30*3) = 90


def test_decorrelated_first_attempt_no_prev():
    cfg = JitterConfig(strategy="decorrelated", max_delay=60.0)
    rng = random.Random(3)
    # prev_delay=0 → upper = max(base, 0) = base, so result == base
    result = apply_jitter(5.0, cfg, prev_delay=0.0, rng=rng)
    assert result == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# parse_jitter helper
# ---------------------------------------------------------------------------

def test_parse_jitter_defaults_to_full():
    cfg = parse_jitter(None)
    assert cfg.strategy == "full"


def test_parse_jitter_respects_strategy():
    cfg = parse_jitter("half", max_delay=30.0)
    assert cfg.strategy == "half"
    assert cfg.max_delay == 30.0
