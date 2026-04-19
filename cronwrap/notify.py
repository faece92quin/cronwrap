"""Notification channels: stdout summary, webhook POST, and email dispatch."""
from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional

from cronwrap.metrics import ExecutionMetrics, to_dict

log = logging.getLogger(__name__)


@dataclass
class NotifyConfig:
    webhook_url: Optional[str] = None
    webhook_headers: dict = field(default_factory=dict)
    email_on_failure: bool = False
    email_on_success: bool = False
    timeout: int = 10


def post_webhook(url: str, payload: dict, headers: dict, timeout: int = 10) -> bool:
    """POST JSON payload to a webhook URL. Returns True on success."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except urllib.error.URLError as exc:
        log.warning("Webhook delivery failed: %s", exc)
        return False


def notify(metrics: ExecutionMetrics, cfg: NotifyConfig) -> None:
    """Dispatch notifications based on config and outcome."""
    if cfg.webhook_url:
        payload = to_dict(metrics)
        ok = post_webhook(cfg.webhook_url, payload, cfg.webhook_headers, cfg.timeout)
        log.debug("Webhook sent=%s url=%s", ok, cfg.webhook_url)
