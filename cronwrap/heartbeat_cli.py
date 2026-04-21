"""CLI helpers for heartbeat configuration (parsed from cronwrap CLI flags)."""

import argparse
from typing import List, Optional

from cronwrap.heartbeat import Heartbeat, make_heartbeat


def add_heartbeat_args(parser: argparse.ArgumentParser) -> None:
    """Attach heartbeat-related arguments to *parser*."""
    grp = parser.add_argument_group("heartbeat")
    grp.add_argument(
        "--heartbeat-url",
        metavar="URL",
        default=None,
        help="URL to GET periodically while the job runs (e.g. a healthcheck endpoint).",
    )
    grp.add_argument(
        "--heartbeat-interval",
        metavar="SECONDS",
        type=float,
        default=30.0,
        help="Seconds between heartbeat pings (default: 30).",
    )


def heartbeat_from_args(args: argparse.Namespace) -> Optional[Heartbeat]:
    """Build a :class:`Heartbeat` from parsed CLI *args*, or return ``None``."""
    url: Optional[str] = getattr(args, "heartbeat_url", None)
    interval: float = getattr(args, "heartbeat_interval", 30.0)

    def _on_error(exc: Exception) -> None:  # pragma: no cover
        # Best-effort: log to stderr so it doesn't silently vanish.
        import sys
        print(f"[cronwrap] heartbeat ping failed: {exc}", file=sys.stderr)

    return make_heartbeat(url, interval=interval, on_error=_on_error)


def build_heartbeat_parser() -> argparse.ArgumentParser:
    """Standalone parser used in tests and documentation generation."""
    p = argparse.ArgumentParser(
        prog="cronwrap-heartbeat",
        description="Heartbeat configuration reference.",
    )
    add_heartbeat_args(p)
    return p
