"""Utilities for validating and describing cron schedule expressions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import re

CRON_FIELDS = ["minute", "hour", "day_of_month", "month", "day_of_week"]
_FIELD_RE = re.compile(
    r"^(\*|\*/[1-9]\d*|[0-9]{1,2}(-[0-9]{1,2})?(,[0-9]{1,2}(-[0-9]{1,2})?)*)$"
)


@dataclass
class CronExpression:
    raw: str
    minute: str
    hour: str
    day_of_month: str
    month: str
    day_of_week: str

    def describe(self) -> str:
        if self.raw == "* * * * *":
            return "every minute"
        parts = []
        if self.minute != "*":
            parts.append(f"minute={self.minute}")
        if self.hour != "*":
            parts.append(f"hour={self.hour}")
        if self.day_of_month != "*":
            parts.append(f"dom={self.day_of_month}")
        if self.month != "*":
            parts.append(f"month={self.month}")
        if self.day_of_week != "*":
            parts.append(f"dow={self.day_of_week}")
        return "cron(" + ", ".join(parts) + ")" if parts else "every minute"


def parse_cron(expression: str) -> CronExpression:
    """Parse and validate a 5-field cron expression."""
    fields = expression.strip().split()
    if len(fields) != 5:
        raise ValueError(
            f"Expected 5 cron fields, got {len(fields)}: {expression!r}"
        )
    for name, value in zip(CRON_FIELDS, fields):
        if not _FIELD_RE.match(value):
            raise ValueError(f"Invalid cron field '{name}': {value!r}")
    return CronExpression(raw=expression, minute=fields[0], hour=fields[1],
                          day_of_month=fields[2], month=fields[3],
                          day_of_week=fields[4])


def validate_cron(expression: str) -> Optional[str]:
    """Return an error message string, or None if valid."""
    try:
        parse_cron(expression)
        return None
    except ValueError as exc:
        return str(exc)
