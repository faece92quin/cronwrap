"""Tests for cronwrap.concurrency."""
from __future__ import annotations

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from cronwrap.concurrency import (
    ConcurrencyConfig,
    ConcurrencyLimitExceeded,
    _load_active,
    _save_active,
    _state_path,
    check_concurrency,
    concurrency_slot,
    parse_concurrency,
)


@pytest.fixture()
def sdir(tmp_path: Path) -> str:
    return str(tmp_path)


def _cfg(sdir: str, max_concurrent: int = 2) -> ConcurrencyConfig:
    return ConcurrencyConfig(job_name="test-job", max_concurrent=max_concurrent, state_dir=sdir)


def test_first_run_allowed(sdir: str) -> None:
    cfg = _cfg(sdir)
    active = check_concurrency(cfg)
    assert active == []


def test_within_limit_allowed(sdir: str) -> None:
    cfg = _cfg(sdir, max_concurrent=2)
    path = _state_path(cfg)
    _save_active(path, [os.getpid()])
    active = check_concurrency(cfg)  # 1 alive, limit 2 → OK
    assert len(active) == 1


def test_exceeds_limit_raises(sdir: str) -> None:
    cfg = _cfg(sdir, max_concurrent=1)
    path = _state_path(cfg)
    _save_active(path, [os.getpid()])
    with pytest.raises(ConcurrencyLimitExceeded):
        check_concurrency(cfg)


def test_dead_pids_not_counted(sdir: str) -> None:
    cfg = _cfg(sdir, max_concurrent=1)
    path = _state_path(cfg)
    _save_active(path, [999999999])  # Almost certainly dead
    # Should not raise because the dead PID is filtered out
    active = check_concurrency(cfg)
    assert active == []


def test_concurrency_slot_registers_and_releases(sdir: str) -> None:
    cfg = _cfg(sdir, max_concurrent=2)
    path = _state_path(cfg)
    with concurrency_slot(cfg):
        active = _load_active(path)
        assert os.getpid() in active
    active_after = _load_active(path)
    assert os.getpid() not in active_after


def test_concurrency_slot_releases_on_exception(sdir: str) -> None:
    cfg = _cfg(sdir, max_concurrent=2)
    path = _state_path(cfg)
    with pytest.raises(RuntimeError):
        with concurrency_slot(cfg):
            raise RuntimeError("boom")
    assert os.getpid() not in _load_active(path)


def test_parse_concurrency_none_returns_none() -> None:
    assert parse_concurrency(None) is None


def test_parse_concurrency_empty_returns_none() -> None:
    assert parse_concurrency("") is None


def test_parse_concurrency_valid_int() -> None:
    assert parse_concurrency("3") == 3
    assert parse_concurrency(1) == 1


def test_parse_concurrency_zero_raises() -> None:
    with pytest.raises(ValueError):
        parse_concurrency(0)


def test_parse_concurrency_invalid_raises() -> None:
    with pytest.raises(ValueError):
        parse_concurrency("abc")
