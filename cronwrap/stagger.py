"""Stagger: randomised start-delay to spread concurrent cron jobs.

Usage::

    cfg = parse_stagger("30s")          # up to 30-second random delay
    actual_delay = compute_stagger(cfg)  # draw a uniform sample
    apply_stagger(cfg)                   # sleep for the drawn delay
"""
from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StaggerConfig:
    """Configuration for a stagger window."""

    max_seconds: float
    seed: Optional[int] = field(default=None)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_SUFFIX_MAP = {
    "s": 1,
    "sec": 1,
    "m": 60,
    "min": 60,
    "h": 3600,
    "hr": 3600,
}
_PATTERN = re.compile(
    r"^(?P<value>[0-9]+(?:\.[0-9]+)?)\s*(?P<unit>[a-zA-Z]*)$"
)


def parse_stagger(value: Optional[str]) -> Optional[StaggerConfig]:
    """Parse a human-readable stagger string such as '30s', '2m', or '120'.

    Returns *None* when *value* is ``None`` or an empty string.
    Raises ``ValueError`` for unrecognised formats.
    """
    if not value:
        return None

    m = _PATTERN.match(value.strip())
    if not m:
        raise ValueError(f"Cannot parse stagger value: {value!r}")

    numeric = float(m.group("value"))
    unit = m.group("unit").lower()

    if unit == "":
        multiplier = 1
    elif unit in _SUFFIX_MAP:
        multiplier = _SUFFIX_MAP[unit]
    else:
        raise ValueError(f"Unknown time unit {unit!r} in stagger value: {value!r}")

    return StaggerConfig(max_seconds=numeric * multiplier)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def compute_stagger(cfg: StaggerConfig) -> float:
    """Return a random delay in seconds drawn uniformly from [0, max_seconds]."""
    rng = random.Random(cfg.seed)
    return rng.uniform(0.0, cfg.max_seconds)


def apply_stagger(cfg: StaggerConfig, *, _sleep=time.sleep) -> float:
    """Sleep for a random delay and return the actual number of seconds slept."""
    delay = compute_stagger(cfg)
    _sleep(delay)
    return delay
