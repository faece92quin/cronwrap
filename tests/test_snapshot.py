"""Tests for cronwrap.snapshot."""
import json
import time
import pytest

from cronwrap.snapshot import (
    Snapshot,
    build_snapshot,
    save_snapshot,
    load_snapshot,
    _snapshot_path,
)


@pytest.fixture()
def base_dir(tmp_path):
    return str(tmp_path)


def _make(job_name="backup", exit_code=0, attempt=1, **kw):
    now = time.time()
    return build_snapshot(
        job_name=job_name,
        command="/usr/bin/backup",
        started_at=now - 5,
        finished_at=now,
        exit_code=exit_code,
        stdout="all good",
        stderr="",
        attempt=attempt,
        **kw,
    )


def test_build_snapshot_preview_truncated():
    snap = build_snapshot(
        job_name="j",
        command="cmd",
        started_at=0.0,
        finished_at=1.0,
        exit_code=0,
        stdout="x" * 1000,
        stderr="",
        preview_chars=100,
    )
    assert len(snap.stdout_preview) == 100


def test_duration_calculated():
    snap = _make()
    assert snap.duration_seconds is not None
    assert snap.duration_seconds == pytest.approx(5.0, abs=0.1)


def test_succeeded_true_on_zero_exit():
    assert _make(exit_code=0).succeeded is True


def test_succeeded_false_on_nonzero_exit():
    assert _make(exit_code=1).succeeded is False


def test_succeeded_none_when_no_exit_code():
    snap = _make()
    snap.finished_at = None
    snap.exit_code = None
    assert snap.succeeded is None


def test_save_and_load_roundtrip(base_dir):
    snap = _make(job_name="my-job", tags=["prod"], labels={"env": "production"})
    save_snapshot(snap, base_dir)
    loaded = load_snapshot("my-job", base_dir)
    assert loaded is not None
    assert loaded.job_name == "my-job"
    assert loaded.exit_code == 0
    assert loaded.tags == ["prod"]
    assert loaded.labels == {"env": "production"}


def test_save_writes_derived_fields(base_dir):
    snap = _make(job_name="j2")
    path = save_snapshot(snap, base_dir)
    data = json.loads(path.read_text())
    assert "duration_seconds" in data
    assert "succeeded" in data


def test_load_returns_none_when_missing(base_dir):
    assert load_snapshot("nonexistent", base_dir) is None


def test_snapshot_path_safe_name(base_dir):
    path = _snapshot_path(base_dir, "my job/name")
    assert "/" not in path.name
    assert " " not in path.name
