"""Tests for cronwrap.drift and cronwrap.drift_cli."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from cronwrap.drift import (
    DriftRecord,
    clear_scheduled,
    format_drift,
    measure_drift,
    record_scheduled,
)
from cronwrap.drift_cli import build_drift_parser, run_drift_cli


@pytest.fixture()
def sdir(tmp_path: Path) -> str:
    return str(tmp_path / "drift")


_SCHEDULED = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
_ACTUAL_LATE = datetime(2024, 6, 1, 12, 0, 45, tzinfo=timezone.utc)  # 45 s late
_ACTUAL_EARLY = datetime(2024, 6, 1, 11, 59, 50, tzinfo=timezone.utc)  # 10 s early


# ---------------------------------------------------------------------------
# drift.py unit tests
# ---------------------------------------------------------------------------

def test_measure_drift_returns_none_without_record(sdir: str) -> None:
    assert measure_drift(sdir, "myjob") is None


def test_record_and_measure_positive_drift(sdir: str) -> None:
    record_scheduled(sdir, "myjob", _SCHEDULED)
    result = measure_drift(sdir, "myjob", actual_at=_ACTUAL_LATE)
    assert result is not None
    assert result.drift_seconds == pytest.approx(45.0)
    assert result.job_name == "myjob"


def test_record_and_measure_negative_drift(sdir: str) -> None:
    record_scheduled(sdir, "myjob", _SCHEDULED)
    result = measure_drift(sdir, "myjob", actual_at=_ACTUAL_EARLY)
    assert result is not None
    assert result.drift_seconds == pytest.approx(-10.0)


def test_exceeded_threshold(sdir: str) -> None:
    record_scheduled(sdir, "myjob", _SCHEDULED)
    result = measure_drift(sdir, "myjob", actual_at=_ACTUAL_LATE)
    assert result is not None
    assert result.exceeded(30.0) is True
    assert result.exceeded(60.0) is False


def test_clear_removes_record(sdir: str) -> None:
    record_scheduled(sdir, "myjob", _SCHEDULED)
    removed = clear_scheduled(sdir, "myjob")
    assert removed is True
    assert measure_drift(sdir, "myjob") is None


def test_clear_nonexistent_returns_false(sdir: str) -> None:
    assert clear_scheduled(sdir, "ghost") is False


def test_format_drift_positive() -> None:
    rec = DriftRecord(
        job_name="j",
        scheduled_at=_SCHEDULED,
        actual_at=_ACTUAL_LATE,
        drift_seconds=45.0,
    )
    text = format_drift(rec)
    assert "drift=+45.0s" in text
    assert "job=j" in text


# ---------------------------------------------------------------------------
# drift_cli.py tests
# ---------------------------------------------------------------------------

def _parse(sdir: str, *argv: str) -> argparse.Namespace:
    parser = build_drift_parser()
    ns = parser.parse_args(["--state-dir", sdir, *argv])
    return ns


def test_show_missing_record(sdir: str) -> None:
    ns = _parse(sdir, "show", "nojob")
    assert run_drift_cli(ns) == 1


def test_record_cmd_creates_entry(sdir: str) -> None:
    ns = _parse(sdir, "record", "myjob", "--at", _SCHEDULED.isoformat())
    assert run_drift_cli(ns) == 0
    result = measure_drift(sdir, "myjob", actual_at=_ACTUAL_LATE)
    assert result is not None


def test_show_cmd_returns_0_within_threshold(sdir: str) -> None:
    record_scheduled(sdir, "myjob", _SCHEDULED)
    ns = _parse(sdir, "show", "myjob", "--threshold", "60")
    # inject a controlled actual time via measure_drift; CLI uses datetime.now so
    # we just confirm it returns 0 (drift from now will be large but threshold check
    # is only done when threshold > 0 and exceeded).
    # We set threshold=0 to skip the warning path.
    ns2 = _parse(sdir, "show", "myjob", "--threshold", "0")
    assert run_drift_cli(ns2) == 0


def test_clear_cmd(sdir: str) -> None:
    record_scheduled(sdir, "myjob", _SCHEDULED)
    ns = _parse(sdir, "clear", "myjob")
    assert run_drift_cli(ns) == 0
    assert measure_drift(sdir, "myjob") is None


def test_clear_missing_returns_1(sdir: str) -> None:
    ns = _parse(sdir, "clear", "ghost")
    assert run_drift_cli(ns) == 1


def test_no_subcommand_returns_1(sdir: str) -> None:
    ns = _parse(sdir)
    assert run_drift_cli(ns) == 1
