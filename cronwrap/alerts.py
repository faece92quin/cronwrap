"""Alerting module for cronwrap — sends notifications on job failure."""

from __future__ import annotations

import smtplib
import logging
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    """Configuration for email alerts."""
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_addr: str = "cronwrap@localhost"
    to_addrs: list[str] = field(default_factory=list)
    use_tls: bool = False


def build_email(subject: str, body: str, config: AlertConfig) -> MIMEText:
    """Build a MIMEText email message."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = config.from_addr
    msg["To"] = ", ".join(config.to_addrs)
    return msg


def send_email_alert(subject: str, body: str, config: AlertConfig) -> bool:
    """Send an email alert. Returns True on success, False on failure."""
    if not config.to_addrs:
        logger.warning("No recipients configured; skipping alert.")
        return False
    try:
        smtp_cls = smtplib.SMTP
        with smtp_cls(config.smtp_host, config.smtp_port) as server:
            if config.use_tls:
                server.starttls()
            if config.smtp_user and config.smtp_password:
                server.login(config.smtp_user, config.smtp_password)
            msg = build_email(subject, body, config)
            server.sendmail(config.from_addr, config.to_addrs, msg.as_string())
        logger.info("Alert sent to %s", config.to_addrs)
        return True
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to send alert: %s", exc)
        return False


def make_failure_alerter(
    config: AlertConfig,
    job_name: str = "cron job",
    sender: Callable[[str, str, AlertConfig], bool] = send_email_alert,
) -> Callable[..., None]:
    """Return an on_failure callback suitable for run_with_retry."""

    def _alert(result) -> None:  # type: ignore[type-arg]
        subject = f"[cronwrap] {job_name} failed (exit {result.returncode})"
        body = (
            f"Job '{job_name}' failed after {result.attempt} attempt(s).\n\n"
            f"Command stdout:\n{result.stdout}\n\n"
            f"Command stderr:\n{result.stderr}\n"
        )
        sender(subject, body, config)

    return _alert
