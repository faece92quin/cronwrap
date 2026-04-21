"""Circuit breaker to skip job execution after repeated failures."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class CircuitOpen(Exception):
    """Raised when the circuit is open and execution should be skipped."""


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: Optional[float] = None
    last_failure_at: Optional[float] = None


def _state_path(state_dir: str, job_name: str) -> Path:
    safe = job_name.replace(os.sep, "_").replace(" ", "_")
    return Path(state_dir) / f"{safe}.circuit.json"


def _load_state(path: Path) -> CircuitState:
    if not path.exists():
        return CircuitState()
    try:
        data = json.loads(path.read_text())
        return CircuitState(
            failures=data.get("failures", 0),
            opened_at=data.get("opened_at"),
            last_failure_at=data.get("last_failure_at"),
        )
    except (json.JSONDecodeError, OSError):
        return CircuitState()


def _save_state(path: Path, state: CircuitState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "failures": state.failures,
        "opened_at": state.opened_at,
        "last_failure_at": state.last_failure_at,
    }))


def check_circuit(
    state_dir: str,
    job_name: str,
    threshold: int = 3,
    recovery_seconds: float = 300.0,
    now: Optional[float] = None,
) -> CircuitState:
    """Raise CircuitOpen if the circuit is open and recovery window hasn't passed."""
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    ts = now if now is not None else time.time()
    path = _state_path(state_dir, job_name)
    state = _load_state(path)
    if state.opened_at is not None:
        elapsed = ts - state.opened_at
        if elapsed < recovery_seconds:
            remaining = recovery_seconds - elapsed
            raise CircuitOpen(
                f"Circuit open for '{job_name}': {remaining:.0f}s remaining before retry."
            )
        # Recovery window passed — reset to half-open (allow one attempt)
        state.failures = threshold - 1
        state.opened_at = None
        _save_state(path, state)
    return state


def record_circuit_outcome(
    state_dir: str,
    job_name: str,
    succeeded: bool,
    threshold: int = 3,
    now: Optional[float] = None,
) -> None:
    """Update circuit state after a job run."""
    ts = now if now is not None else time.time()
    path = _state_path(state_dir, job_name)
    state = _load_state(path)
    if succeeded:
        state.failures = 0
        state.opened_at = None
    else:
        state.failures += 1
        state.last_failure_at = ts
        if state.failures >= threshold:
            state.opened_at = ts
    _save_state(path, state)
