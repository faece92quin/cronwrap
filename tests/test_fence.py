"""Tests for cronwrap.fence and cronwrap.fence_cli."""
from __future__ import annotations

import argparse
from datetime import datetime

import pytest

from cronwrap.fence import (
    FenceConfig,
    FenceViolation,
    check_fence,
    parse_fence,
)
from cronwrap.fence_cli import build_fence_parser, run_fence_cli


# ---------------------------------------------------------------------------
# parse_fence
# ---------------------------------------------------------------------------

def test_parse_fence_none_when_both_none():
    assert parse_fence(None, None) is None


def test_parse_fence_not_before_only():
    cfg = parse_fence("2024-01-01", None)
    assert cfg is not None
    assert cfg.not_before is not None
    assert cfg.not_after is None


def test_parse_fence_not_after_only():
    cfg = parse_fence(None, "2099-12-31")
    assert cfg is not None
    assert cfg.not_after is not None


def test_parse_fence_invalid_date_raises():
    with pytest.raises(ValueError):
        parse_fence("01-01-2024", None)


# ---------------------------------------------------------------------------
# check_fence
# ---------------------------------------------------------------------------

def _dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def test_check_fence_within_range_ok():
    cfg = FenceConfig(not_before=_dt("2024-01-01").date(), not_after=_dt("2099-12-31").date())
    check_fence(cfg, now=_dt("2025-06-15"))  # should not raise


def test_check_fence_before_not_before_raises():
    cfg = FenceConfig(not_before=_dt("2030-01-01").date())
    with pytest.raises(FenceViolation, match="not allowed before"):
        check_fence(cfg, now=_dt("2025-01-01"))


def test_check_fence_after_not_after_raises():
    cfg = FenceConfig(not_after=_dt("2020-12-31").date())
    with pytest.raises(FenceViolation, match="not allowed after"):
        check_fence(cfg, now=_dt("2025-01-01"))


def test_check_fence_on_boundary_allowed():
    d = _dt("2025-06-01").date()
    cfg = FenceConfig(not_before=d, not_after=d)
    check_fence(cfg, now=_dt("2025-06-01"))  # exact boundary — allowed


# ---------------------------------------------------------------------------
# fence_cli
# ---------------------------------------------------------------------------

def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    build_fence_parser(sub)
    return p


def test_cli_show_no_fence(capsys):
    p = _make_parser()
    args = p.parse_args(["fence", "show"])
    rc = run_fence_cli(args)
    assert rc == 0
    assert "No fence configured" in capsys.readouterr().out


def test_cli_show_with_bounds(capsys):
    p = _make_parser()
    args = p.parse_args(["fence", "show", "--not-before", "2024-01-01", "--not-after", "2099-12-31"])
    rc = run_fence_cli(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "2024-01-01" in out
    assert "2099-12-31" in out


def test_cli_check_allowed(capsys):
    p = _make_parser()
    args = p.parse_args(["fence", "check", "--not-before", "2020-01-01", "--at", "2025-06-15"])
    rc = run_fence_cli(args)
    assert rc == 0
    assert "ALLOWED" in capsys.readouterr().out


def test_cli_check_blocked(capsys):
    p = _make_parser()
    args = p.parse_args(["fence", "check", "--not-after", "2020-12-31", "--at", "2025-06-15"])
    rc = run_fence_cli(args)
    assert rc == 1
    assert "BLOCKED" in capsys.readouterr().out


def test_cli_check_no_fence(capsys):
    p = _make_parser()
    args = p.parse_args(["fence", "check"])
    rc = run_fence_cli(args)
    assert rc == 0
    assert "always allowed" in capsys.readouterr().out
