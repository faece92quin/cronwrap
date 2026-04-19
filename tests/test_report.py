"""Tests for cronwrap.report."""
import pytest
from cronwrap.report import format_report, print_report
from cronwrap.metrics import ExecutionMetrics


def _make_metrics(**kwargs):
    defaults = dict(
        exit_code=0,
        duration_seconds=1.234,
        attempt=1,
        stdout_bytes=11,
        stderr_bytes=0,
        stdout_tail="hello world",
        stderr_tail="",
        succeeded=True,
    )
    defaults.update(kwargs)
    return ExecutionMetrics(**defaults)


def test_format_report_success_contains_status():
    r = format_report(_make_metrics())
    assert "SUCCESS" in r
    assert "FAILURE" not in r


def test_format_report_failure_contains_status():
    r = format_report(_make_metrics(exit_code=1, succeeded=False))
    assert "FAILURE" in r


def test_format_report_includes_duration():
    r = format_report(_make_metrics(duration_seconds=3.5))
    assert "3.500s" in r


def test_format_report_includes_job_name():
    r = format_report(_make_metrics(), job_name="backup")
    assert "backup" in r


def test_format_report_unnamed_when_no_job_name():
    r = format_report(_make_metrics())
    assert "(unnamed)" in r


def test_format_report_shows_stdout_tail():
    r = format_report(_make_metrics(stdout_bytes=5, stdout_tail="hello"))
    assert "hello" in r


def test_format_report_hides_empty_stderr():
    r = format_report(_make_metrics(stderr_bytes=0, stderr_tail=""))
    assert "Errors" not in r


def test_print_report_outputs(capsys):
    print_report(_make_metrics(), job_name="myjob")
    out = capsys.readouterr().out
    assert "myjob" in out
    assert "SUCCESS" in out
