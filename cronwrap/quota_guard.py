"""Middleware that enforces per-job execution quotas before running a command."""
from __future__ import annotations

import argparse
from typing import Callable, Optional

from cronwrap.quota import QuotaConfig, QuotaExceeded, check_quota, record_quota_run


def quota_guard_config_from_args(args: argparse.Namespace) -> Optional[QuotaConfig]:
    """Build a QuotaConfig from parsed CLI args, or None if quota is not configured."""
    max_runs = getattr(args, "quota_max_runs", None)
    window = getattr(args, "quota_window", None)
    job_name = getattr(args, "job", None) or getattr(args, "name", None)

    if max_runs is None or window is None or not job_name:
        return None

    state_dir = getattr(args, "state_dir", None)
    kwargs = {"max_runs": int(max_runs), "window_seconds": int(window), "job": job_name}
    if state_dir:
        kwargs["state_dir"] = state_dir
    return QuotaConfig(**kwargs)


def make_quota_guard(
    config: QuotaConfig,
    on_exceeded: Optional[Callable[[QuotaExceeded], None]] = None,
) -> Callable[[Callable[[], int]], int]:
    """Return a guard that enforces *config* around a callable.

    Parameters
    ----------
    config:
        Quota configuration describing the job, window and limit.
    on_exceeded:
        Optional callback invoked when the quota is breached.  Receives the
        ``QuotaExceeded`` exception.  If *None* the exception is re-raised.

    Returns
    -------
    A decorator / wrapper that accepts a zero-argument callable returning an
    int exit code and enforces the quota around it.
    """
    def guard(fn: Callable[[], int]) -> int:
        try:
            check_quota(config)
        except QuotaExceeded as exc:
            if on_exceeded is not None:
                on_exceeded(exc)
                return 1
            raise
        result = fn()
        record_quota_run(config)
        return result

    return guard


def add_quota_guard_args(parser: argparse.ArgumentParser) -> None:
    """Attach quota-guard CLI flags to *parser*."""
    grp = parser.add_argument_group("quota guard")
    grp.add_argument(
        "--quota-max-runs",
        metavar="N",
        type=int,
        default=None,
        help="Maximum number of executions allowed within the quota window.",
    )
    grp.add_argument(
        "--quota-window",
        metavar="SECONDS",
        type=int,
        default=None,
        help="Rolling window size in seconds for the quota counter.",
    )
