"""Cooldown: enforce a minimum gap between successive runs of a job."""

import json
import time
from pathlib import Path
from typing import Optional


class CooldownActive(Exception):
    """Raised when a job is run before its cooldown period has elapsed."""


def _cooldown_path(state_dir: str, job_name: str) -> Path:
    return Path(state_dir) / f"{job_name}.cooldown.json"


def _load_last(path: Path) -> Optional[float]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return float(data["last_run"])
    except (KeyError, ValueError, OSError, json.JSONDecodeError):
        return None


def _save_last(path: Path, ts: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_run": ts}))


def check_cooldown(
    job_name: str,
    cooldown_seconds: int,
    state_dir: str = "/tmp/cronwrap/cooldown",
    now: Optional[float] = None,
) -> None:
    """Raise CooldownActive if not enough time has passed since the last run."""
    now = now or time.time()
    path = _cooldown_path(state_dir, job_name)
    last = _load_last(path)
    if last is not None:
        elapsed = now - last
        if elapsed < cooldown_seconds:
            remaining = cooldown_seconds - elapsed
            raise CooldownActive(
                f"{job_name} is in cooldown for {remaining:.1f}s more"
            )
    _save_last(path, now)


def reset_cooldown(
    job_name: str,
    state_dir: str = "/tmp/cronwrap/cooldown",
) -> None:
    """Remove the cooldown state for a job."""
    path = _cooldown_path(state_dir, job_name)
    if path.exists():
        path.unlink()
