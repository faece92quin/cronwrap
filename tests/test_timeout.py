"""Tests for cronwrap.timeout."""

import time
import pytest

from cronwrap.timeout import TimeoutExpired, parse_timeout, time_limit


# ---------------------------------------------------------------------------
# parse_timeout
# ---------------------------------------------------------------------------

def test_parse_timeout_none_returns_none():
    assert parse_timeout(None) is None


def test_parse_timeout_empty_returns_none():
    assert parse_timeout("") is None


def test_parse_timeout_plain_int():
    assert parse_timeout("30") == 30


def test_parse_timeout_seconds_suffix():
    assert parse_timeout("45s") == 45


def test_parse_timeout_minutes_suffix():
    assert parse_timeout("2m") == 120


def test_parse_timeout_hours_suffix():
    assert parse_timeout("1h") == 3600


def test_parse_timeout_invalid_raises():
    with pytest.raises(ValueError):
        parse_timeout("abc")


# ---------------------------------------------------------------------------
# time_limit
# ---------------------------------------------------------------------------

def test_time_limit_none_does_not_raise():
    with time_limit(None):
        pass  # should complete normally


def test_time_limit_zero_does_not_raise():
    with time_limit(0):
        pass


def test_time_limit_completes_within_limit():
    with time_limit(5):
        time.sleep(0.01)


def test_time_limit_raises_on_expiry():
    with pytest.raises(TimeoutExpired) as exc_info:
        with time_limit(1):
            time.sleep(3)
    assert exc_info.value.seconds == 1


def test_timeout_expired_message():
    err = TimeoutExpired(10)
    assert "10" in str(err)
