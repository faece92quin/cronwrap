"""Tests for cronwrap.audit."""
import time
import pytest
from cronwrap.audit import AuditEntry, record_audit, load_audit, last_audit


def _entry(job="myjob", exit_code=0, attempt=1, offset=0.0):
    now = time.time() + offset
    return AuditEntry(
        job_name=job,
        command="echo hi",
        started_at=now,
        finished_at=now + 1.5,
        exit_code=exit_code,
        attempt=attempt,
    )


def test_record_creates_file(tmp_path):
    e = _entry()
    path = record_audit(e, str(tmp_path))
    assert path.exists()


def test_load_returns_entries(tmp_path):
    record_audit(_entry(), str(tmp_path))
    record_audit(_entry(), str(tmp_path))
    entries = load_audit(str(tmp_path))
    assert len(entries) == 2


def test_load_filters_by_job(tmp_path):
    record_audit(_entry(job="alpha"), str(tmp_path))
    record_audit(_entry(job="beta"), str(tmp_path))
    entries = load_audit(str(tmp_path), job_name="alpha")
    assert all(e["job_name"] == "alpha" for e in entries)
    assert len(entries) == 1


def test_entry_duration(tmp_path):
    record_audit(_entry(), str(tmp_path))
    entries = load_audit(str(tmp_path))
    assert abs(entries[0]["duration"] - 1.5) < 0.01


def test_entry_succeeded_flag(tmp_path):
    record_audit(_entry(exit_code=0), str(tmp_path))
    record_audit(_entry(exit_code=1), str(tmp_path))
    entries = load_audit(str(tmp_path))
    assert entries[0]["succeeded"] is True
    assert entries[1]["succeeded"] is False


def test_last_audit_returns_most_recent(tmp_path):
    record_audit(_entry(exit_code=0), str(tmp_path))
    record_audit(_entry(exit_code=2), str(tmp_path))
    last = last_audit(str(tmp_path), "myjob")
    assert last["exit_code"] == 2


def test_last_audit_none_when_empty(tmp_path):
    assert last_audit(str(tmp_path), "ghost") is None
