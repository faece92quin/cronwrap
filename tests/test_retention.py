"""Tests for cronwrap.retention."""
import time
from pathlib import Path

import pytest

from cronwrap.retention import (
    RetentionConfig,
    RetentionError,
    apply_retention,
    list_files_by_mtime,
    parse_retention,
)


# ---------------------------------------------------------------------------
# parse_retention
# ---------------------------------------------------------------------------

def test_parse_retention_none_when_both_none():
    assert parse_retention(None, None) is None


def test_parse_retention_plain_seconds():
    cfg = parse_retention("3600", None)
    assert cfg is not None
    assert cfg.max_age_seconds == 3600.0


def test_parse_retention_days_suffix():
    cfg = parse_retention("7d", None)
    assert cfg.max_age_seconds == pytest.approx(7 * 86400)


def test_parse_retention_hours_suffix():
    cfg = parse_retention("2h", None)
    assert cfg.max_age_seconds == pytest.approx(7200)


def test_parse_retention_minutes_suffix():
    cfg = parse_retention("30m", None)
    assert cfg.max_age_seconds == pytest.approx(1800)


def test_parse_retention_seconds_suffix():
    cfg = parse_retention("90s", None)
    assert cfg.max_age_seconds == pytest.approx(90)


def test_parse_retention_max_count_only():
    cfg = parse_retention(None, 10)
    assert cfg.max_count == 10
    assert cfg.max_age_seconds is None


def test_parse_retention_negative_age_raises():
    with pytest.raises(RetentionError):
        parse_retention("-5s", None)


def test_parse_retention_negative_count_raises():
    with pytest.raises(RetentionError):
        parse_retention(None, -1)


# ---------------------------------------------------------------------------
# apply_retention — age-based pruning
# ---------------------------------------------------------------------------

def _write(path: Path, content: str = "x") -> Path:
    path.write_text(content)
    return path


def test_apply_retention_removes_old_files(tmp_path):
    now = time.time()
    old = _write(tmp_path / "old.json")
    new = _write(tmp_path / "new.json")
    # backdate old file
    os.utime = __import__("os").utime
    import os
    os.utime(old, (now - 7200, now - 7200))

    cfg = RetentionConfig(max_age_seconds=3600)
    deleted = apply_retention(tmp_path, cfg, now=now)
    assert old in deleted
    assert not old.exists()
    assert new.exists()


def test_apply_retention_keeps_within_age(tmp_path):
    cfg = RetentionConfig(max_age_seconds=86400)
    deleted = apply_retention(tmp_path, cfg)
    assert deleted == []


# ---------------------------------------------------------------------------
# apply_retention — count-based pruning
# ---------------------------------------------------------------------------

def test_apply_retention_keeps_n_most_recent(tmp_path):
    import os
    now = time.time()
    files = []
    for i in range(5):
        f = _write(tmp_path / f"run_{i}.json")
        os.utime(f, (now + i, now + i))
        files.append(f)

    cfg = RetentionConfig(max_count=3)
    deleted = apply_retention(tmp_path, cfg, now=now + 10)
    assert len(deleted) == 2
    assert files[0] in deleted
    assert files[1] in deleted
    for f in files[2:]:
        assert f.exists()


def test_apply_retention_nonexistent_dir_returns_empty(tmp_path):
    cfg = RetentionConfig(max_count=5)
    result = apply_retention(tmp_path / "no_such_dir", cfg)
    assert result == []
