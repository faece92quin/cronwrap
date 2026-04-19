"""Tests for cronwrap.filter."""

import pytest
from cronwrap.filter import FilterConfig, filter_lines, truncate, apply_filters


def _cfg(**kw) -> FilterConfig:
    return FilterConfig(**kw)


def test_filter_lines_no_patterns():
    text = "hello\nworld\n"
    assert filter_lines(text, _cfg()) == text


def test_filter_lines_removes_matching():
    text = "INFO: ok\nDEBUG: noise\nINFO: done\n"
    result = filter_lines(text, _cfg(suppress_patterns=[r"^DEBUG"]))
    assert "DEBUG" not in result
    assert "INFO: ok" in result
    assert "INFO: done" in result


def test_filter_lines_multiple_patterns():
    text = "keep\nremove_a\nremove_b\nkeep2\n"
    result = filter_lines(text, _cfg(suppress_patterns=[r"remove_a", r"remove_b"]))
    assert result == "keep\nkeep2\n"


def test_filter_lines_regex_pattern():
    text = "error 404\nok 200\nerror 500\n"
    result = filter_lines(text, _cfg(suppress_patterns=[r"error \d+"]))
    assert result == "ok 200\n"


def test_truncate_short_text():
    text = "hello"
    assert truncate(text, 100) == text


def test_truncate_long_text():
    text = "a" * 200
    result = truncate(text, 50)
    assert len(result.encode("utf-8")) > 50  # notice appended
    assert "[...output truncated]" in result
    assert result.startswith("a" * 50)


def test_apply_filters_both():
    text = "keep\nspam line\n" + "x" * 300
    cfg = _cfg(suppress_patterns=[r"spam"], max_output_bytes=20)
    result = apply_filters(text, cfg)
    assert "spam" not in result
    assert "[...output truncated]" in result


def test_apply_filters_only_truncate():
    text = "a" * 500
    cfg = _cfg(max_output_bytes=10)
    result = apply_filters(text, cfg)
    assert "[...output truncated]" in result


def test_apply_filters_none():
    text = "clean output\n"
    assert apply_filters(text, _cfg()) == text
