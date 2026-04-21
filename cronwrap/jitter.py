"""Jitter utilities for retry delays — prevents thundering-herd when many
jobs restart simultaneously after a shared outage."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

JitterStrategy = Literal["none", "full", "half", "decorrelated"]

_VALID_STRATEGIES: frozenset[str] = frozenset({"none", "full", "half", "decorrelated"})


@dataclass
class JitterConfig:
    strategy: JitterStrategy = "full"
    max_delay: float = 60.0  # seconds — hard ceiling after jitter

    def __post_init__(self) -> None:
        if self.strategy not in _VALID_STRATEGIES:
            raise ValueError(
                f"Unknown jitter strategy {self.strategy!r}. "
                f"Valid options: {sorted(_VALID_STRATEGIES)}"
            )
        if self.max_delay <= 0:
            raise ValueError("max_delay must be positive")


def apply_jitter(
    delay: float,
    cfg: JitterConfig,
    *,
    prev_delay: float = 0.0,
    rng: random.Random | None = None,
) -> float:
    """Return a jittered version of *delay* according to *cfg*.

    Args:
        delay:      The base delay (e.g. from BackoffConfig.compute_delay).
        cfg:        Jitter configuration.
        prev_delay: The previous sleep duration — used by the 'decorrelated'
                    strategy (pass 0 for the first attempt).
        rng:        Optional seeded Random instance for deterministic tests.

    Returns:
        A non-negative float, capped at *cfg.max_delay*.
    """
    r = rng or random.Random()

    if cfg.strategy == "none":
        result = delay
    elif cfg.strategy == "full":
        result = r.uniform(0, delay)
    elif cfg.strategy == "half":
        half = delay / 2.0
        result = half + r.uniform(0, half)
    elif cfg.strategy == "decorrelated":
        # AWS-style decorrelated jitter: sleep = rand(base, prev * 3)
        base = delay
        upper = max(base, prev_delay * 3)
        result = r.uniform(base, upper)
    else:  # pragma: no cover
        result = delay

    return min(max(result, 0.0), cfg.max_delay)


def parse_jitter(strategy: str | None, max_delay: float = 60.0) -> JitterConfig:
    """Build a JitterConfig from a CLI/config string, defaulting to 'full'."""
    return JitterConfig(strategy=strategy or "full", max_delay=max_delay)  # type: ignore[arg-type]
