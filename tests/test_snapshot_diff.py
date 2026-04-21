"""Tests for cronwrap.snapshot_diff."""
import time
import pytest

from cronwrap.snapshot import build_snapshot
from cronwrap.snapshot_diff import diff_snapshots, format_diff


def _snap(exit_code=0, duration=5.0, attempt=1, tags=None, labels=None):
    now = time.time()
    return build_snapshot(
        job_name="job",
        command="cmd",
        started_at=now - duration,
        finished_at=now,
        exit_code=exit_code,
        stdout="",
        stderr="",
        attempt=attempt,
        tags=tags or [],
        labels=labels or {},
    )


def test_no_change_detected():
    prev = _snap(exit_code=0)
    curr = _snap(exit_code=0)
    diff = diff_snapshots(prev, curr)
    assert not diff.status_changed
    assert not diff.recovered
    assert not diff.degraded


def test_status_changed_on_exit_code_change():
    diff = diff_snapshots(_snap(exit_code=0), _snap(exit_code=1))
    assert diff.status_changed


def test_degraded_flag():
    diff = diff_snapshots(_snap(exit_code=0), _snap(exit_code=1))
    assert diff.degraded
    assert not diff.recovered


def test_recovered_flag():
    diff = diff_snapshots(_snap(exit_code=1), _snap(exit_code=0))
    assert diff.recovered
    assert not diff.degraded


def test_duration_delta_positive_when_slower():
    diff = diff_snapshots(_snap(duration=3.0), _snap(duration=8.0))
    assert diff.duration_delta == pytest.approx(5.0, abs=0.1)


def test_duration_delta_negative_when_faster():
    diff = diff_snapshots(_snap(duration=10.0), _snap(duration=4.0))
    assert diff.duration_delta is not None
    assert diff.duration_delta < 0


def test_label_changes_detected():
    prev = _snap(labels={"env": "staging", "team": "ops"})
    curr = _snap(labels={"env": "production"})
    diff = diff_snapshots(prev, curr)
    assert "env" in diff.label_changes
    assert diff.label_changes["env"] == ("staging", "production")
    assert "team" in diff.label_changes
    assert diff.label_changes["team"] == ("ops", None)


def test_tag_changes_detected():
    prev = _snap(tags=["prod", "nightly"])
    curr = _snap(tags=["prod", "weekly"])
    diff = diff_snapshots(prev, curr)
    assert "weekly" in diff.tag_changes["added"]
    assert "nightly" in diff.tag_changes["removed"]


def test_format_diff_no_changes():
    diff = diff_snapshots(_snap(), _snap())
    result = format_diff(diff)
    assert "No significant changes" in result


def test_format_diff_includes_degraded():
    diff = diff_snapshots(_snap(exit_code=0), _snap(exit_code=1))
    result = format_diff(diff)
    assert "DEGRADED" in result


def test_format_diff_includes_recovered():
    diff = diff_snapshots(_snap(exit_code=1), _snap(exit_code=0))
    result = format_diff(diff)
    assert "RECOVERED" in result
