"""Tests for cronwrap.checkpoint_cli."""

from __future__ import annotations

import argparse

import pytest

from cronwrap.checkpoint import save_checkpoint
from cronwrap.checkpoint_cli import (
    build_checkpoint_parser,
    run_checkpoint_cli,
)


@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path / "cp")


def _parse(sdir: str, *argv: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    build_checkpoint_parser(sub)
    args = parser.parse_args(["checkpoint", *argv])
    args.state_dir = sdir
    return args


def test_list_no_checkpoints(sdir, capsys):
    args = _parse(sdir, "list", "myjob")
    rc = run_checkpoint_cli(args)
    assert rc == 0
    assert "No checkpoints" in capsys.readouterr().out


def test_list_shows_names(sdir, capsys):
    save_checkpoint(sdir, "myjob", "step1", 1)
    save_checkpoint(sdir, "myjob", "step2", 2)
    args = _parse(sdir, "list", "myjob")
    rc = run_checkpoint_cli(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "step1" in out
    assert "step2" in out


def test_show_existing(sdir, capsys):
    save_checkpoint(sdir, "myjob", "cursor", 42)
    args = _parse(sdir, "show", "myjob", "cursor")
    rc = run_checkpoint_cli(args)
    assert rc == 0
    assert "42" in capsys.readouterr().out


def test_show_missing_returns_1(sdir, capsys):
    args = _parse(sdir, "show", "myjob", "ghost")
    rc = run_checkpoint_cli(args)
    assert rc == 1


def test_clear_existing(sdir, capsys):
    save_checkpoint(sdir, "myjob", "pos", 7)
    args = _parse(sdir, "clear", "myjob", "pos")
    rc = run_checkpoint_cli(args)
    assert rc == 0
    assert "Cleared" in capsys.readouterr().out


def test_clear_missing_returns_1(sdir, capsys):
    args = _parse(sdir, "clear", "myjob", "nope")
    rc = run_checkpoint_cli(args)
    assert rc == 1
