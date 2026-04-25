"""Tests for cronwrap.quota_cli."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pytest

from cronwrap.quota import _quota_path, _save_timestamps
from cronwrap.quota_cli import build_quota_parser, run_quota_cli


@pytest.fixture()
def sdir(tmp_path: Path) -> str:
    return str(tmp_path / "quota")


def _parse(args: list, sdir: str) -> argparse.Namespace:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_quota_parser(sub)
    ns = root.parse_args(args)
    # inject tmp state_dir
    ns.state_dir = sdir
    return ns


def test_show_no_history(sdir: str, capsys) -> None:
    ns = _parse(["quota", "show", "myjob"], sdir)
    rc = run_quota_cli(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Runs used: 0" in out


def test_show_with_history(sdir: str, capsys) -> None:
    now = time.time()
    path = _quota_path(sdir, "myjob")
    _save_timestamps(path, [now - 10, now - 5])
    ns = _parse(["quota", "show", "myjob"], sdir)
    rc = run_quota_cli(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Runs used: 2" in out
    assert "Resets in" in out


def test_reset_existing(sdir: str, capsys) -> None:
    path = _quota_path(sdir, "myjob")
    _save_timestamps(path, [1000.0])
    ns = _parse(["quota", "reset", "myjob"], sdir)
    rc = run_quota_cli(ns)
    assert rc == 0
    assert not path.exists()
    assert "cleared" in capsys.readouterr().out


def test_reset_nonexistent(sdir: str, capsys) -> None:
    ns = _parse(["quota", "reset", "ghost"], sdir)
    rc = run_quota_cli(ns)
    assert rc == 0
    assert "No quota history" in capsys.readouterr().out
