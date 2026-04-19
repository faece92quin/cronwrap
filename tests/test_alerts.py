"""Tests for cronwrap.alerts."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cronwrap.alerts import (
    AlertConfig,
    build_email,
    make_failure_alerter,
    send_email_alert,
)


@pytest.fixture()
def cfg() -> AlertConfig:
    return AlertConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_addr="alert@example.com",
        to_addrs=["ops@example.com"],
        use_tls=True,
    )


def test_build_email_headers(cfg: AlertConfig) -> None:
    msg = build_email("Test subject", "Test body", cfg)
    assert msg["Subject"] == "Test subject"
    assert msg["From"] == "alert@example.com"
    assert "ops@example.com" in msg["To"]


def test_send_email_no_recipients() -> None:
    cfg = AlertConfig(to_addrs=[])
    result = send_email_alert("subject", "body", cfg)
    assert result is False


def test_send_email_success(cfg: AlertConfig) -> None:
    with patch("cronwrap.alerts.smtplib.SMTP") as mock_smtp:
        instance = MagicMock()
        mock_smtp.return_value.__enter__ = lambda s: instance
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        result = send_email_alert("hi", "body", cfg)
    assert result is True


def test_make_failure_alerter_calls_sender(cfg: AlertConfig) -> None:
    fake_sender = MagicMock(return_value=True)
    alerter = make_failure_alerter(cfg, job_name="backup", sender=fake_sender)

    fake_result = MagicMock(returncode=1, attempt=3, stdout="out", stderr="err")
    alerter(fake_result)

    fake_sender.assert_called_once()
    subject, body, sent_cfg = fake_sender.call_args[0]
    assert "backup" in subject
    assert "3 attempt" in body
    assert sent_cfg is cfg


def test_make_failure_alerter_subject_contains_exit_code(cfg: AlertConfig) -> None:
    fake_sender = MagicMock(return_value=True)
    alerter = make_failure_alerter(cfg, job_name="sync", sender=fake_sender)
    fake_result = MagicMock(returncode=2, attempt=1, stdout="", stderr="")
    alerter(fake_result)
    subject = fake_sender.call_args[0][0]
    assert "exit 2" in subject
