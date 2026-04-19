"""Tests for cronwrap.audit_report."""
import time
import pytest
from cronwrap.audit import AuditEntry, record_audit
from cronwrap.audit_report import compute_audit_summary, format_audit_report


def _entry(job="job1", exit_code=0):
    now = time.time()
    return AuditEntry(
        job_name=job,
        command="true",
        started_at=now,
        finished_at=now + 2.0,
        exit_code=exit_code,
        attempt=1,
    )


def test_no_entries_returns_zero_total(tmp_path):
    s = compute_audit_summary(str(tmp_path), "missing")
    assert s["total_runs"] == 0


def test_summary_counts(tmp_path):
    for _ in range(3):
        record_audit(_entry(exit_code=0), str(tmp_path))
    record_audit(_entry(exit_code=1), str(tmp_path))
    s = compute_audit_summary(str(tmp_path), "job1")
    assert s["total_runs"] == 4
    assert s["successes"] == 3
    assert s["failures"] == 1


def test_success_rate(tmp_path):
    record_audit(_entry(exit_code=0), str(tmp_path))
    record_audit(_entry(exit_code=1), str(tmp_path))
    s = compute_audit_summary(str(tmp_path), "job1")
    assert s["success_rate"] == 0.5


def test_avg_duration(tmp_path):
    record_audit(_entry(), str(tmp_path))
    s = compute_audit_summary(str(tmp_path), "job1")
    assert abs(s["avg_duration_s"] - 2.0) < 0.1


def test_format_report_no_entries(tmp_path):
    s = compute_audit_summary(str(tmp_path), "ghost")
    text = format_audit_report(s)
    assert "No audit records" in text


def test_format_report_contains_job_name(tmp_path):
    record_audit(_entry(), str(tmp_path))
    s = compute_audit_summary(str(tmp_path), "job1")
    text = format_audit_report(s)
    assert "job1" in text
    assert "Success rate" in text
