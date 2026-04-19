"""Redact sensitive values (secrets, tokens) from command output."""

from __future__ import annotations

import re
from typing import List

_PLACEHOLDER = "***REDACTED***"

# Patterns that look like secrets even without an explicit list
_AUTO_PATTERNS: List[str] = [
    r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[=:]\s*\S+",
]


def redact_values(text: str, secrets: List[str]) -> str:
    """Replace each literal secret string with the placeholder."""
    for secret in secrets:
        if secret:
            text = text.replace(secret, _PLACEHOLDER)
    return text


def redact_patterns(text: str, extra_patterns: List[str] | None = None) -> str:
    """Replace matches of built-in (and optional extra) regex patterns."""
    patterns = _AUTO_PATTERNS + (extra_patterns or [])
    for pat in patterns:
        text = re.sub(pat, _PLACEHOLDER, text)
    return text


def redact(text: str, secrets: List[str] | None = None,
           extra_patterns: List[str] | None = None,
           auto: bool = True) -> str:
    """Full redaction pipeline: literal secrets then pattern-based."""
    if secrets:
        text = redact_values(text, secrets)
    if auto or extra_patterns:
        text = redact_patterns(text, extra_patterns)
    return text
