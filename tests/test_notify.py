"""Tests for cronwrap.notify."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.notify import NotifyConfig, notify, post_webhook
from cronwrap.metrics import ExecutionMetrics


def _make_metrics(exit_code: int = 0) -> ExecutionMetrics:
    return ExecutionMetrics(
        job_name="test-job",
        start_time=0.0,
        end_time=1.5,
        exit_code=exit_code,
        stdout="ok",
        stderr="",
        attempts=1,
    )


class _FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_post_webhook_success():
    with patch("urllib.request.urlopen", return_value=_FakeResponse()) as mock_open:
        result = post_webhook("http://example.com/hook", {"key": "val"}, {})
    assert result is True
    mock_open.assert_called_once()


def test_post_webhook_failure():
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        result = post_webhook("http://example.com/hook", {}, {})
    assert result is False


def test_notify_calls_webhook_when_configured():
    cfg = NotifyConfig(webhook_url="http://example.com/hook")
    with patch("cronwrap.notify.post_webhook", return_value=True) as mock_wh:
        notify(_make_metrics(), cfg)
    mock_wh.assert_called_once()
    payload = mock_wh.call_args[0][1]
    assert payload["job_name"] == "test-job"


def test_notify_skips_webhook_when_not_configured():
    cfg = NotifyConfig(webhook_url=None)
    with patch("cronwrap.notify.post_webhook") as mock_wh:
        notify(_make_metrics(), cfg)
    mock_wh.assert_not_called()
