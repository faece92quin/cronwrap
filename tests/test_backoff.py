"""Tests for cronwrap.backoff."""

import pytest
from cronwrap.backoff import BackoffConfig, compute_delay, parse_backoff


# ---------------------------------------------------------------------------
# BackoffConfig validation
# ---------------------------------------------------------------------------

def test_invalid_strategy_raises():
    with pytest.raises(ValueError, match="strategy"):
        BackoffConfig(strategy="random_walk")


def test_negative_base_raises():
    with pytest.raises(ValueError, match="base"):
        BackoffConfig(base=-1.0)


def test_zero_multiplier_raises():
    with pytest.raises(ValueError, match="multiplier"):
        BackoffConfig(multiplier=0.0)


# ---------------------------------------------------------------------------
# constant strategy
# ---------------------------------------------------------------------------

def test_constant_returns_base():
    cfg = BackoffConfig(strategy="constant", base=5.0)
    assert compute_delay(cfg, 1) == 5.0
    assert compute_delay(cfg, 3) == 5.0


# ---------------------------------------------------------------------------
# linear strategy
# ---------------------------------------------------------------------------

def test_linear_grows_with_attempt():
    cfg = BackoffConfig(strategy="linear", base=1.0, multiplier=3.0)
    assert compute_delay(cfg, 1) == 3.0
    assert compute_delay(cfg, 2) == 6.0
    assert compute_delay(cfg, 3) == 9.0


# ---------------------------------------------------------------------------
# exponential strategy
# ---------------------------------------------------------------------------

def test_exponential_doubles():
    cfg = BackoffConfig(strategy="exponential", base=1.0, multiplier=2.0)
    assert compute_delay(cfg, 1) == 1.0
    assert compute_delay(cfg, 2) == 2.0
    assert compute_delay(cfg, 3) == 4.0
    assert compute_delay(cfg, 4) == 8.0


# ---------------------------------------------------------------------------
# max_delay cap
# ---------------------------------------------------------------------------

def test_max_delay_caps_result():
    cfg = BackoffConfig(strategy="exponential", base=1.0, multiplier=2.0, max_delay=5.0)
    assert compute_delay(cfg, 4) == 5.0   # would be 8 without cap


def test_no_max_delay_uncapped():
    cfg = BackoffConfig(strategy="exponential", base=1.0, multiplier=2.0, max_delay=None)
    assert compute_delay(cfg, 10) == 2.0 ** 9


# ---------------------------------------------------------------------------
# jitter
# ---------------------------------------------------------------------------

def test_jitter_within_bounds():
    cfg = BackoffConfig(strategy="constant", base=10.0, jitter=True)
    for _ in range(50):
        d = compute_delay(cfg, 1)
        assert 0.0 <= d <= 10.0


# ---------------------------------------------------------------------------
# invalid attempt
# ---------------------------------------------------------------------------

def test_attempt_zero_raises():
    cfg = BackoffConfig()
    with pytest.raises(ValueError, match="attempt"):
        compute_delay(cfg, 0)


# ---------------------------------------------------------------------------
# parse_backoff helper
# ---------------------------------------------------------------------------

def test_parse_backoff_returns_config():
    cfg = parse_backoff("linear", 2.0, 1.5, 30.0, False)
    assert isinstance(cfg, BackoffConfig)
    assert cfg.strategy == "linear"
    assert cfg.base == 2.0
    assert cfg.multiplier == 1.5
    assert cfg.max_delay == 30.0
    assert cfg.jitter is False
