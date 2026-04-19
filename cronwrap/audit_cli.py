"""CLI sub-commands for inspecting the audit log."""
from __future__ import annotations

import argparse
import json
import sys

from cronwrap.audit import load_audit, last_audit
from cronwrap.audit_report import compute_audit_summary, format_audit_report

DEFAULT_AUDIT_DIR = "/var/log/cronwrap"


def build_audit_parser(parent: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    p = parent or argparse.ArgumentParser(prog="cronwrap-audit")
    sub = p.add_subparsers(dest="audit_cmd")

    ls = sub.add_parser("list", help="List audit entries")
    ls.add_argument("--job", default=None, help="Filter by job name")
    ls.add_argument("--dir", default=DEFAULT_AUDIT_DIR, dest="audit_dir")
    ls.add_argument("--json", action="store_true", dest="as_json")

    rp = sub.add_parser("report", help="Show summary report for a job")
    rp.add_argument("job", help="Job name")
    rp.add_argument("--dir", default=DEFAULT_AUDIT_DIR, dest="audit_dir")

    last = sub.add_parser("last", help="Show last audit entry for a job")
    last.add_argument("job", help="Job name")
    last.add_argument("--dir", default=DEFAULT_AUDIT_DIR, dest="audit_dir")

    return p


def run_audit_cli(args: argparse.Namespace) -> int:
    cmd = args.audit_cmd

    if cmd == "list":
        entries = load_audit(args.audit_dir, job_name=args.job)
        if args.as_json:
            print(json.dumps(entries, indent=2))
        else:
            for e in entries:
                status = "OK" if e.get("succeeded") else "FAIL"
                print(f"{e['job_name']:20s}  {status}  exit={e['exit_code']}  dur={e.get('duration', 0):.2f}s")
        return 0

    if cmd == "report":
        summary = compute_audit_summary(args.audit_dir, args.job)
        print(format_audit_report(summary))
        return 0

    if cmd == "last":
        entry = last_audit(args.audit_dir, args.job)
        if entry is None:
            print(f"No audit entries for job '{args.job}'", file=sys.stderr)
            return 1
        print(json.dumps(entry, indent=2))
        return 0

    print("No audit sub-command given. Use list, report, or last.", file=sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    _p = build_audit_parser()
    sys.exit(run_audit_cli(_p.parse_args()))
