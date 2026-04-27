"""Tests for cronwrap.quota."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from cronwrap.quota import (
    QuotaConfig,
    QuotaExceeded,
    _quota_path,
    _load_timestamps,
    _save_timestamps,
    check_quota,
    parse_quota,
)


@pytest.fixture()
def sdir(tmp_path: Path) -> str:
    return str(tmp_path / "quota")


def _cfg(sdir: str, max_runs: int = 3, window: int = 60) -> QuotaConfig:
    return QuotaConfig(max_runs=max_runs, window_seconds=window, state_dir=sdir)


def test_first_run_allowed(sdir: str) -> None:
    check_quota(_cfg(sdir), "myjob", now=1000.0)


def test_runs_within_limit_allowed(sdir: str) -> None:
    for i in range(3):
        check_quota(_cfg(sdir), "myjob", now=float(1000 + i))


def test_exceeds_limit_raises(sdir: str) -> None:
    cfg = _cfg(sdir, max_runs=2)
    check_quota(cfg, "myjob", now=1000.0)
    check_quota(cfg, "myjob", now=1001.0)
    with pytest.raises(QuotaExceeded, match="quota"):
        check_quota(cfg, "myjob", now=1002.0)


def test_old_runs_outside_window_not_counted(sdir: str) -> None:
    cfg = _cfg(sdir, max_runs=2, window=60)
    # Two runs far in the past
    check_quota(cfg, "myjob", now=100.0)
    check_quota(cfg, "myjob", now=101.0)
    # Both are outside the window at now=200; should be allowed
    check_quota(cfg, "myjob", now=200.0)


def test_timestamps_persisted(sdir: str) -> None:
    cfg = _cfg(sdir)
    check_quota(cfg, "myjob", now=1000.0)
    path = _quota_path(sdir, "myjob")
    data = json.loads(path.read_text())
    assert 1000.0 in data


def test_quota_error_message_includes_wait(sdir: str) -> None:
    cfg = _cfg(sdir, max_runs=1, window=120)
    check_quota(cfg, "myjob", now=1000.0)
    with pytest.raises(QuotaExceeded, match=r"Retry in ~\d+s"):
        check_quota(cfg, "myjob", now=1010.0)


def test_parse_quota_returns_none_when_missing() -> None:
    assert parse_quota(None, 60, "/tmp") is None
    assert parse_quota(5, None, "/tmp") is None
    assert parse_quota(0, 60, "/tmp") is None


def test_parse_quota_returns_config() -> None:
    cfg = parse_quota(5, 3600, "/tmp/q")
    assert cfg is not None
    assert cfg.max_runs == 5
    assert cfg.window_seconds == 3600


def test_different_jobs_have_independent_quotas(sdir: str) -> None:
    """Quota state for one job must not affect a different job."""
    cfg = _cfg(sdir, max_runs=1)
    check_quota(cfg, "job_a", now=1000.0)
    # job_a is now at its limit, but job_b should be unaffected
    check_quota(cfg, "job_b", now=1000.0)
    with pytest.raises(QuotaExceeded):
        check_quota(cfg, "job_a", now=1001.0)
