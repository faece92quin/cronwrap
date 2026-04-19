"""Human-readable report formatting for cronwrap run results."""
from __future__ import annotations

from typing import Optional

from cronwrap.metrics import ExecutionMetrics


SEP = "-" * 60


def format_report(metrics: ExecutionMetrics, job_name: Optional[str] = None) -> str:
    """Return a formatted multi-line string summarising an execution."""
    name_line = f"Job      : {job_name}" if job_name else "Job      : (unnamed)"
    status = "SUCCESS" if metrics.succeeded else "FAILURE"
    lines = [
        SEP,
        name_line,
        f"Status   : {status}",
        f"Exit code: {metrics.exit_code}",
        f"Duration : {metrics.duration_seconds:.3f}s",
        f"Attempt  : {metrics.attempt}",
        f"Stdout   : {metrics.stdout_bytes} bytes",
        f"Stderr   : {metrics.stderr_bytes} bytes",
    ]
    if metrics.stdout_bytes and metrics.stdout_tail:
        lines.append(f"Output   :\n{metrics.stdout_tail.rstrip()}")
    if metrics.stderr_bytes and metrics.stderr_tail:
        lines.append(f"Errors   :\n{metrics.stderr_tail.rstrip()}")
    lines.append(SEP)
    return "\n".join(lines)


def print_report(metrics: ExecutionMetrics, job_name: Optional[str] = None) -> None:
    """Print the formatted report to stdout."""
    print(format_report(metrics, job_name))
