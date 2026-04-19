"""Tests for the CLI entry point."""
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.cli import build_parser, main
from cronwrap.runner import RunResult


@pytest.fixture()
def success_result():
    return RunResult(success=True, returncode=0, stdout="ok", stderr="", attempt=1)


@pytest.fixture()
def failure_result():
    return RunResult(success=False, returncode=1, stdout="", stderr="err", attempt=3)


def _patch_retry(result):
    return patch("cronwrap.cli.run_with_retry", return_value=result)


def test_build_parser_defaults():
    p = build_parser()
    args = p.parse_args(["echo", "hi"])
    assert args.retries == 0
    assert args.retry_delay == 5.0
    assert args.timeout is None
    assert args.log_level == "INFO"
    assert args.alert_to == []


def test_main_success_returns_0(success_result):
    with _patch_retry(success_result):
        code = main(["echo", "hello"])
    assert code == 0


def test_main_failure_returns_1(failure_result):
    with _patch_retry(failure_result):
        code = main(["false"])
    assert code == 1


def test_main_passes_retries(success_result):
    with _patch_retry(success_result) as mock_retry:
        main(["--retries", "3", "echo", "hi"])
    _, kwargs = mock_retry.call_args
    assert kwargs["attempts"] == 4


def test_main_passes_timeout(success_result):
    with _patch_retry(success_result) as mock_retry:
        main(["--timeout", "30", "sleep", "1"])
    _, kwargs = mock_retry.call_args
    assert kwargs["timeout"] == 30.0


def test_main_no_command_exits():
    with pytest.raises(SystemExit):
        main([])


def test_main_alert_to_creates_alerter(success_result):
    with _patch_retry(success_result) as mock_retry, \
         patch("cronwrap.cli.make_failure_alerter") as mock_alerter:
        mock_alerter.return_value = MagicMock()
        main(["--alert-to", "ops@example.com", "echo", "hi"])
    mock_alerter.assert_called_once()
    _, kwargs = mock_retry.call_args
    assert kwargs["on_failure"] is not None
