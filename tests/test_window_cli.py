"""Tests for cronwrap.window_cli."""

from __future__ import annotations

from unittest.mock import patch
from datetime import datetime

import pytest

from cronwrap.window_cli import run_window_cli


def test_check_inside_window(capsys):
    # 12:00 on a Monday (weekday=0) — well inside 09:00-17:00
    fake_now = datetime(2024, 1, 1, 12, 0)  # Monday
    with patch("cronwrap.window.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        rc = run_window_cli(["check", "09:00-17:00"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ALLOWED" in out


def test_check_outside_window(capsys):
    fake_now = datetime(2024, 1, 1, 8, 0)  # 08:00 — before window
    with patch("cronwrap.window.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        rc = run_window_cli(["check", "09:00-17:00"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "BLOCKED" in out


def test_check_with_at_flag_inside(capsys):
    rc = run_window_cli(["check", "09:00-17:00", "--at", "10:30"])
    assert rc == 0


def test_check_with_at_flag_outside(capsys):
    rc = run_window_cli(["check", "09:00-17:00", "--at", "20:00"])
    assert rc == 1


def test_check_invalid_spec_returns_2(capsys):
    rc = run_window_cli(["check", "badspec"])
    assert rc == 2
    out = capsys.readouterr().out
    assert "ERROR" in out


def test_check_invalid_at_returns_2(capsys):
    rc = run_window_cli(["check", "09:00-17:00", "--at", "not-a-time"])
    assert rc == 2


def test_show_valid_spec(capsys):
    rc = run_window_cli(["show", "08:00-20:00/Mon,Fri"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "08:00" in out
    assert "20:00" in out
    assert "Mon" in out
    assert "Fri" in out


def test_show_no_days(capsys):
    rc = run_window_cli(["show", "06:00-22:00"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "every day" in out


def test_show_invalid_spec_returns_2(capsys):
    rc = run_window_cli(["show", "09:00-17:00/Mon,Xyz"])
    assert rc == 2


def test_no_subcommand_prints_help(capsys):
    rc = run_window_cli([])
    assert rc == 0
