"""Tests for cronwrap.debounce."""
import json
import time
from pathlib import Path

import pytest

from cronwrap.debounce import (
    DebounceConfig,
    DebounceSkipped,
    check_debounce,
    parse_debounce,
    record_debounce_success,
    _debounce_path,
)


@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path / "debounce")


def _cfg(sdir, window=60.0):
    return DebounceConfig(window_seconds=window, state_dir=sdir)


def test_first_run_always_allowed(sdir):
    """No state file means the job has never run — allow it."""
    check_debounce("myjob", _cfg(sdir))  # should not raise


def test_run_after_window_allowed(sdir):
    """A success recorded outside the window should not block execution."""
    cfg = _cfg(sdir, window=30.0)
    past = time.time() - 60.0
    record_debounce_success("myjob", cfg, now=past)
    check_debounce("myjob", cfg)  # should not raise


def test_run_within_window_raises(sdir):
    """A recent success within the window should raise DebounceSkipped."""
    cfg = _cfg(sdir, window=120.0)
    record_debounce_success("myjob", cfg)
    with pytest.raises(DebounceSkipped, match="debounced"):
        check_debounce("myjob", cfg)


def test_debounce_message_includes_remaining(sdir):
    cfg = _cfg(sdir, window=100.0)
    now = time.time()
    record_debounce_success("myjob", cfg, now=now - 10.0)
    with pytest.raises(DebounceSkipped) as exc_info:
        check_debounce("myjob", cfg, now=now)
    assert "retry in" in str(exc_info.value)
    assert "90.0s" in str(exc_info.value)


def test_record_creates_state_file(sdir):
    cfg = _cfg(sdir)
    record_debounce_success("job1", cfg)
    path = _debounce_path("job1", sdir)
    assert path.exists()
    data = json.loads(path.read_text())
    assert "last_success" in data


def test_corrupt_state_treated_as_no_history(sdir, tmp_path):
    cfg = _cfg(sdir)
    path = _debounce_path("job1", sdir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{invalid json")
    check_debounce("job1", cfg)  # should not raise


def test_parse_debounce_seconds(sdir):
    cfg = parse_debounce("45s", state_dir=sdir)
    assert cfg is not None
    assert cfg.window_seconds == 45.0


def test_parse_debounce_minutes(sdir):
    cfg = parse_debounce("2m", state_dir=sdir)
    assert cfg.window_seconds == 120.0


def test_parse_debounce_hours(sdir):
    cfg = parse_debounce("1h", state_dir=sdir)
    assert cfg.window_seconds == 3600.0


def test_parse_debounce_plain_number(sdir):
    cfg = parse_debounce("30", state_dir=sdir)
    assert cfg.window_seconds == 30.0


def test_parse_debounce_none_returns_none(sdir):
    assert parse_debounce(None, state_dir=sdir) is None


def test_parse_debounce_empty_returns_none(sdir):
    assert parse_debounce("", state_dir=sdir) is None
