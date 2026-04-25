"""Tests for cronwrap.sanitize."""

import pytest

from cronwrap.sanitize import (
    SanitizeConfig,
    limit_lines,
    sanitize,
    strip_ansi,
    strip_non_printable,
    truncate_lines,
)


# ---------------------------------------------------------------------------
# strip_ansi
# ---------------------------------------------------------------------------

def test_strip_ansi_color_codes():
    text = "\x1b[31mRed text\x1b[0m"
    assert strip_ansi(text) == "Red text"


def test_strip_ansi_cursor_movement():
    text = "\x1b[2J\x1b[H"
    assert strip_ansi(text) == ""


def test_strip_ansi_no_codes_unchanged():
    text = "plain text\n"
    assert strip_ansi(text) == text


def test_strip_ansi_bold():
    text = "\x1b[1mbold\x1b[22m"
    assert strip_ansi(text) == "bold"


# ---------------------------------------------------------------------------
# strip_non_printable
# ---------------------------------------------------------------------------

def test_strip_non_printable_removes_null():
    assert strip_non_printable("hel\x00lo") == "hello"


def test_strip_non_printable_keeps_newline_and_tab():
    text = "line1\nline2\ttabbed"
    assert strip_non_printable(text) == text


def test_strip_non_printable_with_replacement():
    result = strip_non_printable("a\x01b", replacement="?")
    assert result == "a?b"


# ---------------------------------------------------------------------------
# truncate_lines
# ---------------------------------------------------------------------------

def test_truncate_lines_short_lines_unchanged():
    text = "short\nlines\n"
    assert truncate_lines(text, 80) == text


def test_truncate_lines_cuts_long_line():
    text = "a" * 200 + "\n"
    result = truncate_lines(text, 100)
    lines = result.splitlines()
    assert len(lines[0]) == 100


def test_truncate_lines_preserves_newlines():
    text = "hello\nworld\n"
    result = truncate_lines(text, 3)
    assert result == "hel\nwor\n"


# ---------------------------------------------------------------------------
# limit_lines
# ---------------------------------------------------------------------------

def test_limit_lines_fewer_than_max():
    text = "a\nb\nc\n"
    assert limit_lines(text, 10) == text


def test_limit_lines_trims_excess():
    text = "\n".join(str(i) for i in range(20)) + "\n"
    result = limit_lines(text, 5)
    assert result.count("\n") == 5


# ---------------------------------------------------------------------------
# sanitize (integration)
# ---------------------------------------------------------------------------

def test_sanitize_defaults_strip_ansi_and_control():
    text = "\x1b[32mok\x1b[0m\x00"
    assert sanitize(text) == "ok"


def test_sanitize_no_strip_when_disabled():
    cfg = SanitizeConfig(strip_ansi=False, strip_non_printable=False)
    text = "\x1b[31mhello\x1b[0m"
    assert sanitize(text, cfg) == text


def test_sanitize_max_lines_applied():
    cfg = SanitizeConfig(max_lines=2)
    text = "a\nb\nc\nd\n"
    result = sanitize(text, cfg)
    assert result == "a\nb\n"


def test_sanitize_max_line_length_applied():
    cfg = SanitizeConfig(max_line_length=5)
    text = "hello world\n"
    assert sanitize(text, cfg) == "hello\n"
