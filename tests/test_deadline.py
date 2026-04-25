"""Tests for cronwrap.deadline and cronwrap.deadline_cli."""

from __future__ import annotations

import time
import pytest

from cronwrap.deadline import (
    DeadlineConfig,
    DeadlineMissed,
    check_deadline,
    parse_deadline,
    record_scheduled_time,
    _load_scheduled_time,
    _deadline_path,
)
from cronwrap.deadline_cli import build_deadline_parser, run_deadline_cli


@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# parse_deadline
# ---------------------------------------------------------------------------

def test_parse_deadline_none_returns_none():
    assert parse_deadline(None) is None


def test_parse_deadline_empty_returns_none():
    assert parse_deadline("") is None


def test_parse_deadline_plain_int():
    assert parse_deadline("90") == 90


def test_parse_deadline_seconds_suffix():
    assert parse_deadline("45s") == 45


def test_parse_deadline_minutes_suffix():
    assert parse_deadline("3m") == 180


def test_parse_deadline_hours_suffix():
    assert parse_deadline("2h") == 7200


# ---------------------------------------------------------------------------
# record / load
# ---------------------------------------------------------------------------

def test_record_creates_file(sdir):
    record_scheduled_time(sdir, "myjob", scheduled_at=1000.0)
    path = _deadline_path(sdir, "myjob")
    assert path.exists()


def test_load_returns_recorded_time(sdir):
    record_scheduled_time(sdir, "myjob", scheduled_at=1234.5)
    ts = _load_scheduled_time(sdir, "myjob")
    assert ts == pytest.approx(1234.5)


def test_load_missing_returns_none(sdir):
    assert _load_scheduled_time(sdir, "ghost") is None


# ---------------------------------------------------------------------------
# check_deadline
# ---------------------------------------------------------------------------

def test_check_no_state_skips(sdir):
    cfg = DeadlineConfig(window_seconds=10, job_name="nojob")
    check_deadline(cfg, sdir)  # must not raise


def test_check_within_window_passes(sdir):
    now = time.time()
    record_scheduled_time(sdir, "job1", scheduled_at=now - 5)
    cfg = DeadlineConfig(window_seconds=30, job_name="job1")
    check_deadline(cfg, sdir, now=now)  # 5s elapsed, window=30s


def test_check_past_window_raises(sdir):
    now = time.time()
    record_scheduled_time(sdir, "job2", scheduled_at=now - 120)
    cfg = DeadlineConfig(window_seconds=60, job_name="job2")
    with pytest.raises(DeadlineMissed, match="job2"):
        check_deadline(cfg, sdir, now=now)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse(args):
    parser = build_deadline_parser()
    return parser.parse_args(args)


def test_cli_record_returns_0(sdir):
    ns = _parse(["record", "myjob", "--state-dir", sdir, "--at", "500.0"])
    assert run_deadline_cli(ns) == 0


def test_cli_show_after_record(sdir):
    record_scheduled_time(sdir, "myjob", scheduled_at=999.0)
    ns = _parse(["show", "myjob", "--state-dir", sdir])
    assert run_deadline_cli(ns) == 0


def test_cli_show_missing_returns_1(sdir):
    ns = _parse(["show", "ghost", "--state-dir", sdir])
    assert run_deadline_cli(ns) == 1


def test_cli_clear_existing(sdir):
    record_scheduled_time(sdir, "myjob", scheduled_at=1.0)
    ns = _parse(["clear", "myjob", "--state-dir", sdir])
    assert run_deadline_cli(ns) == 0
    assert _load_scheduled_time(sdir, "myjob") is None


def test_cli_clear_missing_returns_1(sdir):
    ns = _parse(["clear", "ghost", "--state-dir", sdir])
    assert run_deadline_cli(ns) == 1
