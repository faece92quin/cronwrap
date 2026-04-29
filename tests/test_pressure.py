"""Tests for cronwrap.pressure and cronwrap.pressure_cli."""
from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from cronwrap.pressure import (
    PressureConfig,
    PressureExceeded,
    _mem_used_pct,
    check_pressure,
    parse_pressure,
)
from cronwrap.pressure_cli import _cmd_check, _cmd_show, run_pressure_cli


# ---------------------------------------------------------------------------
# check_pressure
# ---------------------------------------------------------------------------

def test_no_thresholds_never_raises():
    cfg = PressureConfig()
    check_pressure(cfg)  # must not raise


def test_load1_below_threshold_ok():
    cfg = PressureConfig(max_load_1=10.0)
    with patch("cronwrap.pressure._load_averages", return_value=(1.0, 0.5, 0.3)):
        check_pressure(cfg)


def test_load1_exceeds_threshold_raises():
    cfg = PressureConfig(max_load_1=2.0)
    with patch("cronwrap.pressure._load_averages", return_value=(3.5, 1.0, 0.8)):
        with pytest.raises(PressureExceeded, match="1-min load"):
            check_pressure(cfg)


def test_load5_exceeds_threshold_raises():
    cfg = PressureConfig(max_load_5=1.5)
    with patch("cronwrap.pressure._load_averages", return_value=(1.0, 2.0, 1.8)):
        with pytest.raises(PressureExceeded, match="5-min load"):
            check_pressure(cfg)


def test_mem_below_threshold_ok():
    cfg = PressureConfig(max_mem_pct=90.0)
    with patch("cronwrap.pressure._mem_used_pct", return_value=50.0):
        check_pressure(cfg)


def test_mem_exceeds_threshold_raises():
    cfg = PressureConfig(max_mem_pct=80.0)
    with patch("cronwrap.pressure._mem_used_pct", return_value=85.0):
        with pytest.raises(PressureExceeded, match="Memory used"):
            check_pressure(cfg)


# ---------------------------------------------------------------------------
# parse_pressure
# ---------------------------------------------------------------------------

def _args(**kwargs):
    ns = argparse.Namespace(max_load_1=None, max_load_5=None, max_mem_pct=None)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_parse_pressure_none_when_no_flags():
    assert parse_pressure(_args()) is None


def test_parse_pressure_builds_config():
    cfg = parse_pressure(_args(max_load_1=4.0, max_mem_pct=75.0))
    assert cfg is not None
    assert cfg.max_load_1 == 4.0
    assert cfg.max_mem_pct == 75.0
    assert cfg.max_load_5 is None


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def test_cmd_show_returns_0(capsys):
    with patch("cronwrap.pressure._load_averages", return_value=(0.5, 0.4, 0.3)), \
         patch("cronwrap.pressure._mem_used_pct", return_value=42.0):
        rc = _cmd_show(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "0.5" in out
    assert "42.0" in out


def test_cmd_show_json(capsys):
    with patch("cronwrap.pressure._load_averages", return_value=(1.0, 0.9, 0.8)), \
         patch("cronwrap.pressure._mem_used_pct", return_value=60.0):
        ns = _args()
        ns.as_json = True
        rc = _cmd_show(ns)
    import json
    data = json.loads(capsys.readouterr().out)
    assert data["load_1"] == 1.0
    assert data["mem_used_pct"] == 60.0
    assert rc == 0


def test_cmd_check_passes(capsys):
    ns = _args(max_load_1=10.0)
    with patch("cronwrap.pressure._load_averages", return_value=(0.1, 0.1, 0.1)):
        rc = _cmd_check(ns)
    assert rc == 0


def test_cmd_check_fails(capsys):
    ns = _args(max_load_1=1.0)
    with patch("cronwrap.pressure._load_averages", return_value=(5.0, 4.0, 3.0)):
        rc = _cmd_check(ns)
    assert rc == 1


def test_run_pressure_cli_show():
    ns = _args()
    ns.pressure_cmd = "show"
    ns.as_json = False
    with patch("cronwrap.pressure._load_averages", return_value=(0.0, 0.0, 0.0)), \
         patch("cronwrap.pressure._mem_used_pct", return_value=0.0):
        assert run_pressure_cli(ns) == 0


def test_run_pressure_cli_unknown_returns_2():
    ns = _args()
    ns.pressure_cmd = "unknown"
    assert run_pressure_cli(ns) == 2
