"""Summarise run history for a job."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from cronwrap.history import load_history


def compute_summary(job_name: str, history_dir: Optional[Path] = None) -> dict:
    """Return aggregate statistics over all recorded runs."""
    records: List[dict] = load_history(job_name, history_dir)
    if not records:
        return {"job": job_name, "total_runs": 0}

    total = len(records)
    successes = sum(1 for r in records if r.get("succeeded"))
    durations = [r["duration"] for r in records if "duration" in r]

    return {
        "job": job_name,
        "total_runs": total,
        "success_count": successes,
        "failure_count": total - successes,
        "success_rate": round(successes / total, 4),
        "avg_duration": round(sum(durations) / len(durations), 4) if durations else None,
        "min_duration": round(min(durations), 4) if durations else None,
        "max_duration": round(max(durations), 4) if durations else None,
        "last_exit_code": records[-1].get("exit_code"),
        "last_timestamp": records[-1].get("timestamp"),
    }


def format_summary(summary: dict) -> str:
    """Return a human-readable summary string."""
    if summary["total_runs"] == 0:
        return f"No history found for job '{summary['job']}'"

    lines = [
        f"Job            : {summary['job']}",
        f"Total runs     : {summary['total_runs']}",
        f"Successes      : {summary['success_count']}",
        f"Failures       : {summary['failure_count']}",
        f"Success rate   : {summary['success_rate'] * 100:.1f}%",
        f"Avg duration   : {summary['avg_duration']}s",
        f"Min / Max      : {summary['min_duration']}s / {summary['max_duration']}s",
        f"Last exit code : {summary['last_exit_code']}",
        f"Last run       : {summary['last_timestamp']}",
    ]
    return "\n".join(lines)
