"""fence.py — Execution fence: prevent a job from running outside a defined
date/time range (start date, end date, or both).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


class FenceViolation(Exception):
    """Raised when the current time is outside the allowed fence."""


@dataclass
class FenceConfig:
    not_before: Optional[date] = None  # inclusive
    not_after: Optional[date] = None   # inclusive


_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _parse_date(value: str) -> date:
    if not _DATE_RE.match(value):
        raise ValueError(f"Invalid date format (expected YYYY-MM-DD): {value!r}")
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_fence(
    not_before: Optional[str],
    not_after: Optional[str],
) -> Optional[FenceConfig]:
    """Return a FenceConfig if either bound is provided, else None."""
    if not not_before and not not_after:
        return None
    return FenceConfig(
        not_before=_parse_date(not_before) if not_before else None,
        not_after=_parse_date(not_after) if not_after else None,
    )


def check_fence(
    cfg: FenceConfig,
    now: Optional[datetime] = None,
) -> None:
    """Raise FenceViolation if *now* is outside the configured fence.

    Args:
        cfg:  The fence configuration.
        now:  Override the current time (useful in tests).
    """
    today = (now or datetime.utcnow()).date()

    if cfg.not_before is not None and today < cfg.not_before:
        raise FenceViolation(
            f"Job is not allowed before {cfg.not_before} (today is {today})"
        )
    if cfg.not_after is not None and today > cfg.not_after:
        raise FenceViolation(
            f"Job is not allowed after {cfg.not_after} (today is {today})"
        )
