"""
cronwrap.labels
~~~~~~~~~~~~~~~
Key-value label support for annotating cron jobs with arbitrary metadata
(e.g. team, env, tier).  Labels are stored as plain dicts and serialised
as "key=value" strings on the CLI.
"""

from __future__ import annotations

from typing import Dict, List, Optional


Labels = Dict[str, str]


def parse_label(raw: str) -> tuple[str, str]:
    """Parse a single ``key=value`` string into a (key, value) tuple.

    Raises ``ValueError`` if *raw* does not contain exactly one ``=``.
    """
    if "=" not in raw:
        raise ValueError(f"Label {raw!r} must be in 'key=value' format")
    key, _, value = raw.partition("=")
    key = key.strip().lower()
    value = value.strip()
    if not key:
        raise ValueError(f"Label key must not be empty in {raw!r}")
    return key, value


def parse_labels(raw_list: List[str]) -> Labels:
    """Parse a list of ``key=value`` strings into a dict.

    Duplicate keys are overwritten by the last occurrence.
    """
    labels: Labels = {}
    for raw in raw_list:
        k, v = parse_label(raw)
        labels[k] = v
    return labels


def format_labels(labels: Labels) -> List[str]:
    """Serialise a labels dict back to a sorted list of ``key=value`` strings."""
    return [f"{k}={v}" for k, v in sorted(labels.items())]


def labels_match(labels: Labels, required: Labels) -> bool:
    """Return *True* if *labels* contains every key-value pair in *required*."""
    return all(labels.get(k) == v for k, v in required.items())


def merge_labels(*sources: Optional[Labels]) -> Labels:
    """Merge multiple label dicts left-to-right; later sources win."""
    merged: Labels = {}
    for src in sources:
        if src:
            merged.update(src)
    return merged
