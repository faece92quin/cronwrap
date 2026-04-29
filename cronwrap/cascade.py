"""Cascade: run a sequence of dependent jobs, stopping on first failure."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from cronwrap.runner import RunResult


@dataclass
class CascadeStep:
    name: str
    command: str
    allow_failure: bool = False


@dataclass
class CascadeResult:
    steps: List[str] = field(default_factory=list)
    results: List[RunResult] = field(default_factory=list)
    stopped_at: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.stopped_at is None

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def completed_steps(self) -> int:
        return len(self.results)


def run_cascade(
    steps: List[CascadeStep],
    runner: Callable[[str], RunResult],
    on_step_start: Optional[Callable[[CascadeStep, int], None]] = None,
    on_step_end: Optional[Callable[[CascadeStep, RunResult], None]] = None,
) -> CascadeResult:
    """Execute steps in order, halting on failure unless allow_failure is set."""
    result = CascadeResult(steps=[s.name for s in steps])

    for idx, step in enumerate(steps):
        if on_step_start:
            on_step_start(step, idx)

        run_result = runner(step.command)
        result.results.append(run_result)

        if on_step_end:
            on_step_end(step, run_result)

        if run_result.exit_code != 0 and not step.allow_failure:
            result.stopped_at = step.name
            break

    return result


def parse_cascade_steps(raw: List[dict]) -> List[CascadeStep]:
    """Parse a list of dicts into CascadeStep objects."""
    steps = []
    for item in raw:
        if "name" not in item or "command" not in item:
            raise ValueError(f"Each cascade step needs 'name' and 'command': {item}")
        steps.append(
            CascadeStep(
                name=item["name"],
                command=item["command"],
                allow_failure=bool(item.get("allow_failure", False)),
            )
        )
    return steps


def format_cascade_result(result: CascadeResult) -> str:
    """Return a human-readable summary of a cascade run."""
    lines = []
    for name, r in zip(result.steps, result.results):
        status = "OK" if r.exit_code == 0 else f"FAILED (exit {r.exit_code})"
        lines.append(f"  {name}: {status}")
    if result.stopped_at:
        lines.append(f"Cascade halted at step: {result.stopped_at}")
    else:
        lines.append("Cascade completed successfully.")
    return "\n".join(lines)
