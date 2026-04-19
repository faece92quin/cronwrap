"""Human-readable summary report from ExecutionMetrics."""
from __future__ import annotations

import datetime
from typing import Optional

from cronwrap.metrics import ExecutionMetrics


STATUS_OK = "OK"
STATUS_FAIL = "FAIL"


def format_report(metrics: ExecutionMetrics, label: Optional[str] = None) -> str:
    """Return a multi-line plain-text report for *metrics*."""
    status = STATUS_OK if metrics.succeeded else STATUS_FAIL
    started = datetime.datetime.utcfromtimestamp(metrics.started_at).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    lines = [
        "=" * 52,
        f"  cronwrap execution report{(' — ' + label) if label else ''}",
        "=" * 52,
        f"  Status    : {status}",
        f"  Command   : {metrics.command}",
        f"  Started   : {started}",
        f"  Duration  : {metrics.duration_seconds:.3f}s",
        f"  Exit code : {metrics.exit_code}",
        f"  Attempts  : {metrics.attempts}",
        f"  Stdout    : {metrics.stdout_bytes} bytes",
        f"  Stderr    : {metrics.stderr_bytes} bytes",
    ]
    if metrics.extra:
        lines.append("  Extra     :")
        for k, v in metrics.extra.items():
            lines.append(f"    {k}: {v}")
    lines.append("=" * 52)
    return "\n".join(lines)


def print_report(metrics: ExecutionMetrics, label: Optional[str] = None) -> None:
    print(format_report(metrics, label=label))
