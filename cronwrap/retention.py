"""Retention policy: prune old history/audit/snapshot files by age or count."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class RetentionConfig:
    max_age_seconds: Optional[float] = None  # prune entries older than this
    max_count: Optional[int] = None           # keep only the N most recent files


class RetentionError(Exception):
    """Raised when retention config is invalid."""


def parse_retention(max_age: Optional[str], max_count: Optional[int]) -> Optional[RetentionConfig]:
    """Build a RetentionConfig from CLI-style arguments."""
    if max_age is None and max_count is None:
        return None
    age_seconds: Optional[float] = None
    if max_age:
        max_age = max_age.strip()
        if max_age.endswith("d"):
            age_seconds = float(max_age[:-1]) * 86400
        elif max_age.endswith("h"):
            age_seconds = float(max_age[:-1]) * 3600
        elif max_age.endswith("m"):
            age_seconds = float(max_age[:-1]) * 60
        elif max_age.endswith("s"):
            age_seconds = float(max_age[:-1])
        else:
            age_seconds = float(max_age)
        if age_seconds <= 0:
            raise RetentionError(f"max_age must be positive, got: {max_age!r}")
    if max_count is not None and max_count < 0:
        raise RetentionError(f"max_count must be non-negative, got: {max_count}")
    return RetentionConfig(max_age_seconds=age_seconds, max_count=max_count)


def list_files_by_mtime(directory: Path) -> List[Path]:
    """Return files in *directory* sorted oldest-first by mtime."""
    if not directory.is_dir():
        return []
    files = [p for p in directory.iterdir() if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime)
    return files


def apply_retention(directory: Path, cfg: RetentionConfig, now: Optional[float] = None) -> List[Path]:
    """Delete files in *directory* that violate the retention policy.

    Returns the list of paths that were deleted.
    """
    if now is None:
        now = time.time()
    files = list_files_by_mtime(directory)
    deleted: List[Path] = []

    if cfg.max_age_seconds is not None:
        cutoff = now - cfg.max_age_seconds
        for f in list(files):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                deleted.append(f)
                files.remove(f)

    if cfg.max_count is not None and len(files) > cfg.max_count:
        excess = files[: len(files) - cfg.max_count]
        for f in excess:
            f.unlink()
            deleted.append(f)

    return deleted
