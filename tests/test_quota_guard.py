"""Tests for cronwrap.quota_guard."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.quota import QuotaConfig, QuotaExceeded
from cronwrap.quota_guard import (
    add_quota_guard_args,
    make_quota_guard,
    quota_guard_config_from_args,
)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "quota_max_runs": None,
        "quota_window": None,
        "job": None,
        "state_dir": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# quota_guard_config_from_args
# ---------------------------------------------------------------------------

def test_config_from_args_none_when_not_set():
    args = _make_args()
    assert quota_guard_config_from_args(args) is None


def test_config_from_args_none_when_missing_job():
    args = _make_args(quota_max_runs=5, quota_window=3600)
    assert quota_guard_config_from_args(args) is None


def test_config_from_args_builds_config():
    args = _make_args(quota_max_runs=10, quota_window=86400, job="nightly")
    cfg = quota_guard_config_from_args(args)
    assert cfg is not None
    assert cfg.max_runs == 10
    assert cfg.window_seconds == 86400
    assert cfg.job == "nightly"


def test_config_from_args_uses_state_dir():
    args = _make_args(
        quota_max_runs=3, quota_window=60, job="myjob", state_dir="/tmp/s"
    )
    cfg = quota_guard_config_from_args(args)
    assert cfg.state_dir == "/tmp/s"


# ---------------------------------------------------------------------------
# make_quota_guard
# ---------------------------------------------------------------------------

def _cfg(tmp_path) -> QuotaConfig:
    return QuotaConfig(job="test-job", max_runs=5, window_seconds=3600,
                       state_dir=str(tmp_path))


def test_guard_executes_fn(tmp_path):
    called = []

    def fn():
        called.append(True)
        return 0

    with patch("cronwrap.quota_guard.check_quota"), \
         patch("cronwrap.quota_guard.record_quota_run"):
        guard = make_quota_guard(_cfg(tmp_path))
        rc = guard(fn)

    assert rc == 0
    assert called == [True]


def test_guard_reraises_when_no_callback(tmp_path):
    def fn():  # pragma: no cover
        return 0

    with patch("cronwrap.quota_guard.check_quota",
               side_effect=QuotaExceeded("too many")):
        guard = make_quota_guard(_cfg(tmp_path))
        with pytest.raises(QuotaExceeded):
            guard(fn)


def test_guard_calls_on_exceeded_callback(tmp_path):
    received = []

    def fn():  # pragma: no cover
        return 0

    exc = QuotaExceeded("limit hit")
    with patch("cronwrap.quota_guard.check_quota", side_effect=exc):
        guard = make_quota_guard(_cfg(tmp_path), on_exceeded=received.append)
        rc = guard(fn)

    assert rc == 1
    assert received == [exc]


# ---------------------------------------------------------------------------
# add_quota_guard_args
# ---------------------------------------------------------------------------

def test_add_quota_guard_args_registers_flags():
    parser = argparse.ArgumentParser()
    add_quota_guard_args(parser)
    args = parser.parse_args(["--quota-max-runs", "5", "--quota-window", "3600"])
    assert args.quota_max_runs == 5
    assert args.quota_window == 3600
