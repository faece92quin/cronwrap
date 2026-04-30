"""Token bucket rate limiter for smooth throughput control.

Allows bursting up to `capacity` tokens, refilling at `rate` tokens/second.
State is persisted to disk so limits survive process restarts.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class TokensExhausted(Exception):
    """Raised when the bucket has insufficient tokens."""

    def __init__(self, job: str, available: float, requested: float) -> None:
        self.job = job
        self.available = available
        self.requested = requested
        super().__init__(
            f"Token bucket exhausted for '{job}': "
            f"requested {requested:.2f}, available {available:.2f}"
        )


@dataclass
class TokenBucketConfig:
    job: str
    rate: float          # tokens refilled per second
    capacity: float      # maximum tokens the bucket can hold
    state_dir: str = "/tmp/cronwrap/token_bucket"


def _bucket_path(cfg: TokenBucketConfig) -> Path:
    safe = cfg.job.replace("/", "_").replace(" ", "_")
    return Path(cfg.state_dir) / f"{safe}.json"


def _load_state(path: Path, capacity: float) -> tuple[float, float]:
    """Return (tokens, last_refill_timestamp)."""
    try:
        data = json.loads(path.read_text())
        return float(data["tokens"]), float(data["last_refill"])
    except (FileNotFoundError, KeyError, ValueError):
        return capacity, time.monotonic()


def _save_state(path: Path, tokens: float, last_refill: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"tokens": tokens, "last_refill": last_refill}))


def consume(cfg: TokenBucketConfig, tokens: float = 1.0) -> float:
    """Consume *tokens* from the bucket, refilling first based on elapsed time.

    Returns the number of tokens remaining after consumption.
    Raises TokensExhausted if the bucket cannot satisfy the request.
    """
    path = _bucket_path(cfg)
    now = time.monotonic()
    current_tokens, last_refill = _load_state(path, cfg.capacity)

    elapsed = max(0.0, now - last_refill)
    refilled = min(cfg.capacity, current_tokens + elapsed * cfg.rate)

    if refilled < tokens:
        _save_state(path, refilled, now)
        raise TokensExhausted(cfg.job, refilled, tokens)

    remaining = refilled - tokens
    _save_state(path, remaining, now)
    return remaining


def parse_token_bucket(
    job: str,
    rate: Optional[str],
    capacity: Optional[str],
    state_dir: str = "/tmp/cronwrap/token_bucket",
) -> Optional[TokenBucketConfig]:
    """Build a TokenBucketConfig from CLI-style string arguments."""
    if not rate and not capacity:
        return None
    r = float(rate) if rate else 1.0
    c = float(capacity) if capacity else r * 60
    return TokenBucketConfig(job=job, rate=r, capacity=c, state_dir=state_dir)
