"""Tests for cronwrap.token_bucket."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from cronwrap.token_bucket import (
    TokenBucketConfig,
    TokensExhausted,
    _bucket_path,
    _load_state,
    _save_state,
    consume,
    parse_token_bucket,
)


@pytest.fixture()
def sdir(tmp_path: Path) -> str:
    return str(tmp_path)


def _cfg(sdir: str, rate: float = 1.0, capacity: float = 5.0) -> TokenBucketConfig:
    return TokenBucketConfig(job="test-job", rate=rate, capacity=capacity, state_dir=sdir)


# ---------------------------------------------------------------------------
# _load_state / _save_state
# ---------------------------------------------------------------------------

def test_load_state_missing_file_returns_full_capacity(tmp_path):
    path = tmp_path / "missing.json"
    tokens, _ = _load_state(path, capacity=10.0)
    assert tokens == 10.0


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    _save_state(path, tokens=3.5, last_refill=1234.0)
    tokens, ts = _load_state(path, capacity=10.0)
    assert tokens == pytest.approx(3.5)
    assert ts == pytest.approx(1234.0)


# ---------------------------------------------------------------------------
# consume – happy path
# ---------------------------------------------------------------------------

def test_first_consume_succeeds(sdir):
    cfg = _cfg(sdir, rate=1.0, capacity=5.0)
    remaining = consume(cfg, tokens=1.0)
    assert remaining == pytest.approx(4.0, abs=0.1)


def test_consume_reduces_tokens(sdir):
    cfg = _cfg(sdir, rate=1.0, capacity=5.0)
    consume(cfg, tokens=2.0)
    remaining = consume(cfg, tokens=1.0)
    assert remaining == pytest.approx(2.0, abs=0.1)


def test_consume_full_bucket(sdir):
    cfg = _cfg(sdir, rate=1.0, capacity=5.0)
    remaining = consume(cfg, tokens=5.0)
    assert remaining == pytest.approx(0.0, abs=0.01)


# ---------------------------------------------------------------------------
# consume – exhaustion
# ---------------------------------------------------------------------------

def test_exhausted_raises(sdir):
    cfg = _cfg(sdir, rate=0.0, capacity=2.0)
    consume(cfg, tokens=2.0)  # drain
    with pytest.raises(TokensExhausted) as exc_info:
        consume(cfg, tokens=1.0)
    err = exc_info.value
    assert err.job == "test-job"
    assert err.requested == pytest.approx(1.0)
    assert err.available < 1.0


def test_exhausted_message_contains_job(sdir):
    cfg = _cfg(sdir, rate=0.0, capacity=1.0)
    consume(cfg, tokens=1.0)
    with pytest.raises(TokensExhausted, match="test-job"):
        consume(cfg, tokens=1.0)


def test_state_saved_even_on_exhaustion(sdir):
    cfg = _cfg(sdir, rate=0.0, capacity=2.0)
    consume(cfg, tokens=2.0)
    with pytest.raises(TokensExhausted):
        consume(cfg, tokens=1.0)
    path = _bucket_path(cfg)
    assert path.exists()


# ---------------------------------------------------------------------------
# parse_token_bucket
# ---------------------------------------------------------------------------

def test_parse_none_when_both_none():
    assert parse_token_bucket("job", None, None) is None


def test_parse_rate_only():
    cfg = parse_token_bucket("job", "2.0", None)
    assert cfg is not None
    assert cfg.rate == pytest.approx(2.0)
    assert cfg.capacity == pytest.approx(120.0)  # 60 * rate


def test_parse_rate_and_capacity():
    cfg = parse_token_bucket("job", "0.5", "10")
    assert cfg.rate == pytest.approx(0.5)
    assert cfg.capacity == pytest.approx(10.0)


def test_parse_uses_state_dir():
    cfg = parse_token_bucket("job", "1", "5", state_dir="/custom")
    assert cfg.state_dir == "/custom"
