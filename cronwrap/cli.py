"""CLI entry point for cronwrap."""
import argparse
import sys

from cronwrap.alerts import make_failure_alerter
from cronwrap.logging_setup import configure_logging, get_logger
from cronwrap.retry import run_with_retry
from cronwrap.runner import run_command


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwrap",
        description="Wrap a cron command with logging, retries, and alerts.",
    )
    p.add_argument("command", nargs=argparse.REMAINDER, help="Command to run")
    p.add_argument("--retries", type=int, default=0, help="Number of retry attempts")
    p.add_argument("--retry-delay", type=float, default=5.0, dest="retry_delay")
    p.add_argument("--timeout", type=float, default=None, help="Timeout in seconds")
    p.add_argument("--log-level", default="INFO", dest="log_level")
    p.add_argument("--log-file", default=None, dest="log_file")
    p.add_argument("--json-logs", action="store_true", dest="json_logs")
    p.add_argument("--alert-to", nargs="*", default=[], dest="alert_to")
    p.add_argument("--alert-from", default="cronwrap@localhost", dest="alert_from")
    p.add_argument("--smtp-host", default="localhost", dest="smtp_host")
    p.add_argument("--smtp-port", type=int, default=25, dest="smtp_port")
    p.add_argument("--job-name", default=None, dest="job_name")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    command = [a for a in args.command if a != "--"]
    if not command:
        parser.error("No command provided.")

    configure_logging(
        level=args.log_level,
        json_format=args.json_logs,
        log_file=args.log_file,
    )
    logger = get_logger("cronwrap.cli")

    job_label = args.job_name or " ".join(command)
    logger.info("Starting job", extra={"job": job_label})

    alerter = None
    if args.alert_to:
        from cronwrap.alerts import AlertConfig
        cfg = AlertConfig(
            recipients=args.alert_to,
            sender=args.alert_from,
            smtp_host=args.smtp_host,
            smtp_port=args.smtp_port,
            job_name=job_label,
        )
        alerter = make_failure_alerter(cfg)

    result = run_with_retry(
        command=command,
        attempts=args.retries + 1,
        delay=args.retry_delay,
        timeout=args.timeout,
        on_failure=alerter,
    )

    if result.success:
        logger.info("Job succeeded", extra={"job": job_label, "attempt": result.attempt})
    else:
        logger.error(
            "Job failed",
            extra={"job": job_label, "returncode": result.returncode, "stderr": result.stderr},
        )

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
