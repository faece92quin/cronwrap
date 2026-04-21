"""Compare two snapshots and report meaningful changes between runs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cronwrap.snapshot import Snapshot


@dataclass
class SnapshotDiff:
    status_changed: bool
    previous_exit_code: Optional[int]
    current_exit_code: Optional[int]
    duration_delta: Optional[float]  # seconds; positive = slower
    attempt_changed: bool
    previous_attempt: int
    current_attempt: int
    label_changes: dict  # {key: (old, new)}
    tag_changes: dict  # {"added": [...], "removed": [...]}

    @property
    def recovered(self) -> bool:
        """True when previous run failed and current run succeeded."""
        return (
            self.previous_exit_code is not None
            and self.previous_exit_code != 0
            and self.current_exit_code == 0
        )

    @property
    def degraded(self) -> bool:
        """True when previous run succeeded and current run failed."""
        return (
            self.previous_exit_code == 0
            and self.current_exit_code is not None
            and self.current_exit_code != 0
        )


def diff_snapshots(previous: Snapshot, current: Snapshot) -> SnapshotDiff:
    status_changed = previous.exit_code != current.exit_code

    if previous.duration_seconds is not None and current.duration_seconds is not None:
        duration_delta: Optional[float] = round(
            current.duration_seconds - previous.duration_seconds, 3
        )
    else:
        duration_delta = None

    # Label diff
    label_changes: dict = {}
    all_keys = set(previous.labels) | set(current.labels)
    for key in all_keys:
        old_val = previous.labels.get(key)
        new_val = current.labels.get(key)
        if old_val != new_val:
            label_changes[key] = (old_val, new_val)

    # Tag diff
    prev_tags = set(previous.tags)
    curr_tags = set(current.tags)
    tag_changes = {
        "added": sorted(curr_tags - prev_tags),
        "removed": sorted(prev_tags - curr_tags),
    }

    return SnapshotDiff(
        status_changed=status_changed,
        previous_exit_code=previous.exit_code,
        current_exit_code=current.exit_code,
        duration_delta=duration_delta,
        attempt_changed=previous.attempt != current.attempt,
        previous_attempt=previous.attempt,
        current_attempt=current.attempt,
        label_changes=label_changes,
        tag_changes=tag_changes,
    )


def format_diff(diff: SnapshotDiff) -> str:
    lines: List[str] = []
    if diff.status_changed:
        lines.append(
            f"Status changed: exit {diff.previous_exit_code} -> {diff.current_exit_code}"
        )
    if diff.recovered:
        lines.append("  ✓ Job RECOVERED (was failing, now passing)")
    elif diff.degraded:
        lines.append("  ✗ Job DEGRADED (was passing, now failing)")
    if diff.duration_delta is not None:
        sign = "+" if diff.duration_delta >= 0 else ""
        lines.append(f"Duration delta: {sign}{diff.duration_delta}s")
    if diff.label_changes:
        for key, (old, new) in diff.label_changes.items():
            lines.append(f"Label '{key}': {old!r} -> {new!r}")
    if diff.tag_changes["added"]:
        lines.append(f"Tags added: {', '.join(diff.tag_changes['added'])}")
    if diff.tag_changes["removed"]:
        lines.append(f"Tags removed: {', '.join(diff.tag_changes['removed'])}")
    return "\n".join(lines) if lines else "No significant changes detected."
