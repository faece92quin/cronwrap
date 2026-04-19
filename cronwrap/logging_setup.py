"""Structured logging configuration for cronwrap."""

from __future__ import annotations

import logging
import sys
from typing import Optional


LOG_FORMAT_PLAIN = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_FORMAT_JSON = (
    '{"time": "%(asctime)s", "level": "%(levelname)s",'
    ' "logger": "%(name)s", "message": "%(message)s"}'
)


def configure_logging(
    level: str = "INFO",
    fmt: str = "plain",
    log_file: Optional[str] = None,
) -> None:
    """Configure root logger for cronwrap.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR).
        fmt: 'plain' or 'json'.
        log_file: Optional path to a log file; stdout is always included.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter(
        LOG_FORMAT_JSON if fmt == "json" else LOG_FORMAT_PLAIN
    )

    root = logging.getLogger()
    root.setLevel(numeric_level)
    # Remove existing handlers to avoid duplicate output.
    root.handlers.clear()

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    root.addHandler(stdout_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger under the cronwrap namespace."""
    return logging.getLogger(f"cronwrap.{name}")
