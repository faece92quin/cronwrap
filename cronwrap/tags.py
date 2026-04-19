"""Tag support for labeling and filtering cron jobs."""
from __future__ import annotations

from typing import Iterable


def normalize_tag(tag: str) -> str:
    """Lowercase and strip whitespace from a tag."""
    return tag.strip().lower()


def normalize_tags(tags: Iterable[str]) -> list[str]:
    """Return a sorted, deduplicated list of normalized tags."""
    return sorted({normalize_tag(t) for t in tags if t.strip()})


def tags_match(job_tags: list[str], required: list[str]) -> bool:
    """Return True if all *required* tags are present in *job_tags*."""
    if not required:
        return True
    job_set = set(job_tags)
    return all(normalize_tag(r) in job_set for r in required)


def tags_match_any(job_tags: list[str], candidates: list[str]) -> bool:
    """Return True if at least one candidate tag is present in *job_tags*."""
    if not candidates:
        return True
    job_set = set(job_tags)
    return any(normalize_tag(c) in job_set for c in candidates)


def format_tags(tags: list[str]) -> str:
    """Return a human-readable comma-separated tag string."""
    return ", ".join(tags) if tags else "(none)"


def parse_tags_arg(value: str) -> list[str]:
    """Parse a comma-separated tag string from a CLI argument."""
    return normalize_tags(value.split(","))
