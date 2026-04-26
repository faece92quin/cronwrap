"""Tests for cronwrap.concurrency_middleware."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from cronwrap.concurrency import ConcurrencyConfig, ConcurrencyLimitExceeded
from cronwrap.concurrency_middleware import (
    add_concurrency_args,
    concurrency_config_from_args,
    make_concurrency_guard,
)


def _make_args(**kwargs: object) -> argparse.Namespace:
    defaults = {
        "max_concurrent": None,
        "concurrency_state_dir": "/tmp/cronwrap/concurrency",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_config_from_args_none_when_not_set() -> None:
    args = _make_args(max_concurrent=None)
    assert concurrency_config_from_args(args, "myjob") is None


def test_config_from_args_builds_config() -> None:
    args = _make_args(max_concurrent="2", concurrency_state_dir="/tmp/x")
    cfg = concurrency_config_from_args(args, "myjob")
    assert cfg is not None
    assert cfg.max_concurrent == 2
    assert cfg.job_name == "myjob"
    assert cfg.state_dir == "/tmp/x"


def test_guard_executes_fn(tmp_path: Path) -> None:
    cfg = ConcurrencyConfig(job_name="j", max_concurrent=2, state_dir=str(tmp_path))
    guard = make_concurrency_guard(cfg)
    result = guard(lambda: 42)
    assert result == 42


def test_add_concurrency_args_adds_flags() -> None:
    parser = argparse.ArgumentParser()
    add_concurrency_args(parser)
    args = parser.parse_args(["--max-concurrent", "3"])
    assert args.max_concurrent == "3"


def test_add_concurrency_args_defaults() -> None:
    parser = argparse.ArgumentParser()
    add_concurrency_args(parser)
    args = parser.parse_args([])
    assert args.max_concurrent is None
    assert "cronwrap/concurrency" in args.concurrency_state_dir
