"""Tests for cronwrap.history and cronwrap.summary."""

import pytest
from pathlib import Path

from cronwrap.history import record_run, load_history, last_run
from cronwrap.summary import compute_summary, format_summary


@pytest.fixture()
def hdir(tmp_path: Path) -> Path:
    return tmp_path / "history"


def test_record_creates_file(hdir):
    record_run("myjob", exit_code=0, duration=1.2, history_dir=hdir)
    files = list(hdir.iterdir())
    assert len(files) == 1
    assert files[0].name == "myjob.jsonl"


def test_load_history_returns_records(hdir):
    record_run("myjob", exit_code=0, duration=1.0, history_dir=hdir)
    record_run("myjob", exit_code=1, duration=2.0, history_dir=hdir)
    records = load_history("myjob", hdir)
    assert len(records) == 2
    assert records[0]["exit_code"] == 0
    assert records[1]["exit_code"] == 1


def test_last_run_returns_most_recent(hdir):
    record_run("myjob", exit_code=0, duration=0.5, history_dir=hdir)
    record_run("myjob", exit_code=2, duration=3.0, history_dir=hdir)
    lr = last_run("myjob", hdir)
    assert lr is not None
    assert lr["exit_code"] == 2


def test_last_run_none_when_no_history(hdir):
    assert last_run("ghost", hdir) is None


def test_succeeded_flag(hdir):
    record_run("j", exit_code=0, duration=1.0, history_dir=hdir)
    record_run("j", exit_code=1, duration=1.0, history_dir=hdir)
    records = load_history("j", hdir)
    assert records[0]["succeeded"] is True
    assert records[1]["succeeded"] is False


def test_compute_summary_empty(hdir):
    s = compute_summary("unknown", hdir)
    assert s["total_runs"] == 0


def test_compute_summary_stats(hdir):
    for code, dur in [(0, 1.0), (0, 3.0), (1, 2.0)]:
        record_run("j", exit_code=code, duration=dur, history_dir=hdir)
    s = compute_summary("j", hdir)
    assert s["total_runs"] == 3
    assert s["success_count"] == 2
    assert s["failure_count"] == 1
    assert abs(s["success_rate"] - 2 / 3) < 0.001
    assert s["avg_duration"] == round(2.0, 4)


def test_compute_summary_min_max_duration(hdir):
    """min_duration and max_duration should reflect the shortest and longest runs."""
    for code, dur in [(0, 1.0), (0, 3.0), (1, 2.0)]:
        record_run("j", exit_code=code, duration=dur, history_dir=hdir)
    s = compute_summary("j", hdir)
    assert s["min_duration"] == 1.0
    assert s["max_duration"] == 3.0


def test_format_summary_no_history(hdir):
    out = format_summary(compute_summary("none", hdir))
    assert "No history" in out


def test_format_summary_contains_job_name(hdir):
    record_run("myjob", exit_code=0, duration=1.0, history_dir=hdir)
    out = format_summary(compute_summary("myjob", hdir))
    assert "myjob" in out
    assert "100.0%" in out
