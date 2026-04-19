"""Human-readable summary derived from the audit log."""
from __future__ import annotations

from typing import List

from cronwrap.audit import load_audit


def compute_audit_summary(audit_dir: str, job_name: str) -> dict:
    entries = load_audit(audit_dir, job_name=job_name)
    if not entries:
        return {"job_name": job_name, "total_runs": 0}

    total = len(entries)
    successes = sum(1 for e in entries if e.get("succeeded"))
    failures = total - successes
    durations = [e["duration"] for e in entries if "duration" in e]
    avg_duration = sum(durations) / len(durations) if durations else 0.0
    last = entries[-1]

    return {
        "job_name": job_name,
        "total_runs": total,
        "successes": successes,
        "failures": failures,
        "success_rate": round(successes / total, 4) if total else 0.0,
        "avg_duration_s": round(avg_duration, 3),
        "last_exit_code": last.get("exit_code"),
        "last_run_at": last.get("started_at"),
    }


def format_audit_report(summary: dict) -> str:
    if summary["total_runs"] == 0:
        return f"No audit records found for job '{summary['job_name']}'"
    lines = [
        f"Audit report for job: {summary['job_name']}",
        f"  Total runs     : {summary['total_runs']}",
        f"  Successes      : {summary['successes']}",
        f"  Failures       : {summary['failures']}",
        f"  Success rate   : {summary['success_rate'] * 100:.1f}%",
        f"  Avg duration   : {summary['avg_duration_s']}s",
        f"  Last exit code : {summary['last_exit_code']}",
    ]
    return "\n".join(lines)
