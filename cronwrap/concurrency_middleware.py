"""Middleware helpers for wiring concurrency limits into the main CLI."""
from __future__ import annotations

import argparse
from typing import Callable

from cronwrap.concurrency import (
    ConcurrencyConfig,
    ConcurrencyLimitExceeded,
    concurrency_slot,
    parse_concurrency,
)


def concurrency_config_from_args(
    args: argparse.Namespace,
    job_name: str,
) -> ConcurrencyConfig | None:
    """Build a ConcurrencyConfig from parsed CLI arguments, or None if not set."""
    limit = parse_concurrency(getattr(args, "max_concurrent", None))
    if limit is None:
        return None
    state_dir = getattr(args, "concurrency_state_dir", "/tmp/cronwrap/concurrency")
    return ConcurrencyConfig(
        job_name=job_name,
        max_concurrent=limit,
        state_dir=state_dir,
    )


def make_concurrency_guard(
    cfg: ConcurrencyConfig,
) -> Callable[[Callable[[], int]], int]:
    """Return a wrapper that enforces the concurrency limit around a callable."""

    def guard(fn: Callable[[], int]) -> int:
        with concurrency_slot(cfg):
            return fn()

    return guard


def add_concurrency_args(parser: argparse.ArgumentParser) -> None:
    """Add concurrency-related arguments to an existing argument parser."""
    parser.add_argument(
        "--max-concurrent",
        metavar="N",
        default=None,
        help="Maximum number of simultaneous instances allowed (default: unlimited)",
    )
    parser.add_argument(
        "--concurrency-state-dir",
        default="/tmp/cronwrap/concurrency",
        metavar="DIR",
        help="Directory used to store concurrency state files",
    )
