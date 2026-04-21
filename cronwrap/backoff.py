"""Backoff strategies for retry delays."""

import random
from typing import Optional


class BackoffConfig:
    """Configuration for a backoff strategy."""

    def __init__(
        self,
        strategy: str = "exponential",
        base: float = 1.0,
        multiplier: float = 2.0,
        max_delay: Optional[float] = 60.0,
        jitter: bool = False,
    ):
        allowed = {"constant", "linear", "exponential"}
        if strategy not in allowed:
            raise ValueError(f"strategy must be one of {allowed}, got {strategy!r}")
        if base < 0:
            raise ValueError("base must be >= 0")
        if multiplier <= 0:
            raise ValueError("multiplier must be > 0")
        self.strategy = strategy
        self.base = base
        self.multiplier = multiplier
        self.max_delay = max_delay
        self.jitter = jitter


def compute_delay(config: BackoffConfig, attempt: int) -> float:
    """Return the delay in seconds before the next retry attempt.

    *attempt* is 1-based: the first retry is attempt 1.
    """
    if attempt < 1:
        raise ValueError("attempt must be >= 1")

    if config.strategy == "constant":
        delay = config.base
    elif config.strategy == "linear":
        delay = config.base * config.multiplier * attempt
    else:  # exponential
        delay = config.base * (config.multiplier ** (attempt - 1))

    if config.max_delay is not None:
        delay = min(delay, config.max_delay)

    if config.jitter:
        delay = random.uniform(0.0, delay)

    return delay


def parse_backoff(strategy: str, base: float, multiplier: float,
                  max_delay: Optional[float], jitter: bool) -> BackoffConfig:
    """Convenience constructor used by CLI argument parsing."""
    return BackoffConfig(
        strategy=strategy,
        base=base,
        multiplier=multiplier,
        max_delay=max_delay,
        jitter=jitter,
    )
