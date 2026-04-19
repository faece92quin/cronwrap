"""Tests for cronwrap.logging_setup."""

from __future__ import annotations

import logging
import os
import tempfile

from cronwrap.logging_setup import configure_logging, get_logger


def _reset_root() -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)


def test_configure_logging_sets_level() -> None:
    configure_logging(level="DEBUG")
    assert logging.getLogger().level == logging.DEBUG
    _reset_root()


def test_configure_logging_plain_adds_handler() -> None:
    configure_logging(level="INFO", fmt="plain")
    root = logging.getLogger()
    assert len(root.handlers) >= 1
    _reset_root()


def test_configure_logging_json_format() -> None:
    configure_logging(level="INFO", fmt="json")
    root = logging.getLogger()
    fmt_str = root.handlers[0].formatter._fmt  # type: ignore[union-attr]
    assert "\"level\"" in fmt_str or '"level"' in fmt_str
    _reset_root()


def test_configure_logging_file_handler() -> None:
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
        log_path = f.name
    try:
        configure_logging(level="INFO", log_file=log_path)
        root = logging.getLogger()
        assert len(root.handlers) == 2
    finally:
        _reset_root()
        os.unlink(log_path)


def test_get_logger_namespace() -> None:
    logger = get_logger("runner")
    assert logger.name == "cronwrap.runner"


def test_configure_logging_clears_existing_handlers() -> None:
    configure_logging(level="INFO")
    configure_logging(level="WARNING")
    root = logging.getLogger()
    assert len(root.handlers) == 1
    _reset_root()
