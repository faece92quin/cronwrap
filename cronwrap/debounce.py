"""Debounce logic: skip a run if the last successful run was too recent.

This is distinct from cooldown (which applies to all runs) — debounce only
skips when the *last run succeeded* within the given window.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class DebounceSkipped(Exception):
    """Raised when a job is skipped due to debounce."""


@dataclass
class DebounceConfig:
    window_seconds: float
    state_dir: str = "/tmp/cronwrap/debounce"


def _debounce_path(job_name: str, state_dir: str) -> Path:
    return Path(state_dir) / f"{job_name}.json"


def _load_last_success(path: Path) -> Optional[float]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return float(data["last_success"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return None


def _save_last_success(path: Path, ts: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_success": ts}))


def check_debounce(job_name: str, cfg: DebounceConfig, now: Optional[float] = None) -> None:
    """Raise DebounceSkipped if the last successful run is within the window."""
    if now is None:
        now = time.time()
    path = _debounce_path(job_name, cfg.state_dir)
    last = _load_last_success(path)
    if last is not None:
        elapsed = now - last
        if elapsed < cfg.window_seconds:
            remaining = cfg.window_seconds - elapsed
            raise DebounceSkipped(
                f"Job '{job_name}' debounced: last success {elapsed:.1f}s ago, "
                f"window={cfg.window_seconds}s, retry in {remaining:.1f}s"
            )


def record_debounce_success(job_name: str, cfg: DebounceConfig, now: Optional[float] = None) -> None:
    """Record a successful run timestamp for debounce tracking."""
    if now is None:
        now = time.time()
    path = _debounce_path(job_name, cfg.state_dir)
    _save_last_success(path, now)


def parse_debounce(window: Optional[str], state_dir: str = "/tmp/cronwrap/debounce") -> Optional[DebounceConfig]:
    """Parse a debounce window string like '30s', '5m', '1h' into a DebounceConfig."""
    if not window:
        return None
    window = window.strip()
    if window.endswith("h"):
        seconds = float(window[:-1]) * 3600
    elif window.endswith("m"):
        seconds = float(window[:-1]) * 60
    elif window.endswith("s"):
        seconds = float(window[:-1])
    else:
        seconds = float(window)
    return DebounceConfig(window_seconds=seconds, state_dir=state_dir)
