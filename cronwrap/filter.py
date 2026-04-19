"""Output filtering: suppress noisy stdout/stderr lines via patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FilterConfig:
    suppress_patterns: List[str] = field(default_factory=list)
    max_output_bytes: Optional[int] = None  # truncate if exceeded


def _compile(patterns: List[str]) -> List[re.Pattern]:
    compiled = []
    for p in patterns:
        try:
            compiled.append(re.compile(p))
        except re.error as e:
            raise ValueError(f"Invalid suppress pattern {p!r}: {e}") from e
    return compiled


def filter_lines(text: str, config: FilterConfig) -> str:
    """Remove lines matching any suppress pattern."""
    if not config.suppress_patterns:
        return text
    compiled = _compile(config.suppress_patterns)
    kept = [
        line for line in text.splitlines(keepends=True)
        if not any(rx.search(line) for rx in compiled)
    ]
    return "".join(kept)


def truncate(text: str, max_bytes: int) -> str:
    """Truncate text to at most max_bytes UTF-8 bytes, appending a notice."""
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + "\n[...output truncated]\n"


def apply_filters(text: str, config: FilterConfig) -> str:
    """Apply line filtering then optional byte truncation."""
    result = filter_lines(text, config)
    if config.max_output_bytes is not None:
        result = truncate(result, config.max_output_bytes)
    return result
