"""Middleware helpers that integrate quota checks into the cronwrap run lifecycle."""

from __future__ import annotations

from typing import Callable, Optional

from cronwrap.quota import QuotaConfig, QuotaExceeded, check_quota
from cronwrap.runner import RunResult


def make_quota_guard(
    config: Optional[QuotaConfig],
    job_name: str,
    on_exceeded: Optional[Callable[[str], None]] = None,
) -> Callable[[], Optional[RunResult]]:
    """Return a callable that enforces the quota before a job run.

    Returns None when the job is allowed to proceed, or a synthetic
    RunResult with exit_code=2 when the quota has been exceeded.
    """

    def guard() -> Optional[RunResult]:
        if config is None:
            return None
        try:
            check_quota(config, job_name)
            return None
        except QuotaExceeded as exc:
            msg = str(exc)
            if on_exceeded:
                on_exceeded(msg)
            return RunResult(
                exit_code=2,
                stdout="",
                stderr=msg,
                attempt=1,
            )

    return guard


def quota_config_from_args(
    max_runs: Optional[int],
    window: Optional[int],
    state_dir: str = "/tmp/cronwrap/quota",
) -> Optional[QuotaConfig]:
    """Convenience wrapper used by the CLI to build a QuotaConfig from parsed args."""
    from cronwrap.quota import parse_quota

    return parse_quota(max_runs, window, state_dir)
