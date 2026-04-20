"""Utilities for capturing, splitting, and size-limiting command output."""
from __future__ import annotations

import dataclasses
from typing import Optional


_DEFAULT_MAX_BYTES = 1 * 1024 * 1024  # 1 MiB


@dataclasses.dataclass
class CapturedOutput:
    """Holds the raw stdout and stderr strings from a command run."""

    stdout: str
    stderr: str
    stdout_truncated: bool = False
    stderr_truncated: bool = False

    @property
    def stdout_bytes(self) -> int:
        return len(self.stdout.encode())

    @property
    def stderr_bytes(self) -> int:
        return len(self.stderr.encode())

    @property
    def combined(self) -> str:
        """Return stdout and stderr merged, stderr lines prefixed with [STDERR]."""
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            prefixed = "\n".join(
                f"[STDERR] {line}" for line in self.stderr.splitlines()
            )
            parts.append(prefixed)
        return "\n".join(parts)


def truncate_output(text: str, max_bytes: int) -> tuple[str, bool]:
    """Truncate *text* so that its UTF-8 encoding is at most *max_bytes*.

    Returns ``(possibly_truncated_text, was_truncated)``.
    """
    encoded = text.encode()
    if len(encoded) <= max_bytes:
        return text, False
    truncated = encoded[:max_bytes].decode(errors="ignore")
    return truncated, True


def capture(
    stdout: str,
    stderr: str,
    max_bytes: Optional[int] = _DEFAULT_MAX_BYTES,
) -> CapturedOutput:
    """Build a :class:`CapturedOutput`, optionally truncating each stream.

    Pass *max_bytes=None* to disable truncation.
    """
    if max_bytes is None:
        return CapturedOutput(stdout=stdout, stderr=stderr)

    out, out_trunc = truncate_output(stdout, max_bytes)
    err, err_trunc = truncate_output(stderr, max_bytes)
    return CapturedOutput(
        stdout=out,
        stderr=err,
        stdout_truncated=out_trunc,
        stderr_truncated=err_trunc,
    )
