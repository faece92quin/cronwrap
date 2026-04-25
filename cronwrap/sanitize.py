"""Output sanitization: strip ANSI escape codes and non-printable characters."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# Matches ANSI/VT100 escape sequences (colors, cursor movement, etc.)
_ANSI_ESCAPE_RE = re.compile(
    r"\x1b"
    r"(?:"
    r"[@-Z\\-_]"
    r"|[\[\]()#;?]*"
    r"(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><~]"
    r")"
)

# Matches non-printable ASCII characters except tab (\x09) and newline (\x0a)
_NON_PRINTABLE_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


@dataclass
class SanitizeConfig:
    strip_ansi: bool = True
    strip_non_printable: bool = True
    replacement: str = ""
    max_line_length: Optional[int] = None
    max_lines: Optional[int] = None


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from *text*."""
    return _ANSI_ESCAPE_RE.sub("", text)


def strip_non_printable(text: str, replacement: str = "") -> str:
    """Remove non-printable characters from *text*, keeping tab and newline."""
    return _NON_PRINTABLE_RE.sub(replacement, text)


def truncate_lines(text: str, max_line_length: int) -> str:
    """Truncate each line to *max_line_length* characters."""
    lines = text.splitlines(keepends=True)
    result = []
    for line in lines:
        ending = "\n" if line.endswith("\n") else ""
        body = line.rstrip("\n")
        if len(body) > max_line_length:
            body = body[:max_line_length]
        result.append(body + ending)
    return "".join(result)


def limit_lines(text: str, max_lines: int) -> str:
    """Keep only the first *max_lines* lines of *text*."""
    lines = text.splitlines(keepends=True)
    return "".join(lines[:max_lines])


def sanitize(text: str, cfg: Optional[SanitizeConfig] = None) -> str:
    """Apply all configured sanitization steps to *text*."""
    if cfg is None:
        cfg = SanitizeConfig()
    if cfg.strip_ansi:
        text = strip_ansi(text)
    if cfg.strip_non_printable:
        text = strip_non_printable(text, cfg.replacement)
    if cfg.max_line_length is not None:
        text = truncate_lines(text, cfg.max_line_length)
    if cfg.max_lines is not None:
        text = limit_lines(text, cfg.max_lines)
    return text
