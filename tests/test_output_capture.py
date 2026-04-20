"""Tests for cronwrap.output_capture."""
import pytest

from cronwrap.output_capture import (
    CapturedOutput,
    capture,
    truncate_output,
)


# ---------------------------------------------------------------------------
# truncate_output
# ---------------------------------------------------------------------------

def test_truncate_output_no_truncation_needed():
    text = "hello world"
    result, truncated = truncate_output(text, max_bytes=1024)
    assert result == text
    assert truncated is False


def test_truncate_output_exact_boundary():
    text = "abcd"  # 4 bytes
    result, truncated = truncate_output(text, max_bytes=4)
    assert result == text
    assert truncated is False


def test_truncate_output_over_limit():
    text = "abcdef"  # 6 bytes
    result, truncated = truncate_output(text, max_bytes=3)
    assert result == "abc"
    assert truncated is True


def test_truncate_output_empty_string():
    result, truncated = truncate_output("", max_bytes=10)
    assert result == ""
    assert truncated is False


# ---------------------------------------------------------------------------
# capture
# ---------------------------------------------------------------------------

def test_capture_no_truncation_when_max_bytes_none():
    big = "x" * 2_000_000
    out = capture(big, "", max_bytes=None)
    assert out.stdout == big
    assert out.stdout_truncated is False


def test_capture_truncates_stdout():
    out = capture("hello world", "err", max_bytes=5)
    assert len(out.stdout.encode()) <= 5
    assert out.stdout_truncated is True
    assert out.stderr_truncated is False


def test_capture_truncates_stderr():
    out = capture("ok", "error output", max_bytes=5)
    assert len(out.stderr.encode()) <= 5
    assert out.stderr_truncated is True


def test_capture_byte_counts():
    out = capture("hello", "bye", max_bytes=None)
    assert out.stdout_bytes == 5
    assert out.stderr_bytes == 3


# ---------------------------------------------------------------------------
# CapturedOutput.combined
# ---------------------------------------------------------------------------

def test_combined_stdout_only():
    out = CapturedOutput(stdout="line1\nline2", stderr="")
    assert out.combined == "line1\nline2"


def test_combined_stderr_prefixed():
    out = CapturedOutput(stdout="", stderr="oops")
    assert "[STDERR] oops" in out.combined


def test_combined_both_streams():
    out = CapturedOutput(stdout="out", stderr="err")
    combined = out.combined
    assert "out" in combined
    assert "[STDERR] err" in combined


def test_combined_empty():
    out = CapturedOutput(stdout="", stderr="")
    assert out.combined == ""
