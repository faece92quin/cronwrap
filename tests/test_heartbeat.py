"""Tests for cronwrap.heartbeat."""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.heartbeat import Heartbeat, make_heartbeat


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hb(url="http://example.com/ping", interval=0.05):
    return Heartbeat(url, interval=interval)


# ---------------------------------------------------------------------------
# make_heartbeat factory
# ---------------------------------------------------------------------------

def test_make_heartbeat_none_when_no_url():
    assert make_heartbeat(None) is None
    assert make_heartbeat("") is None


def test_make_heartbeat_returns_instance():
    hb = make_heartbeat("http://example.com/ping", interval=10)
    assert isinstance(hb, Heartbeat)
    assert hb.url == "http://example.com/ping"
    assert hb.interval == 10


# ---------------------------------------------------------------------------
# Heartbeat lifecycle
# ---------------------------------------------------------------------------

def test_start_spawns_thread():
    hb = _make_hb()
    with patch.object(hb, "_ping"):
        hb.start()
        assert hb._thread is not None
        assert hb._thread.is_alive()
        hb.stop()


def test_stop_joins_thread():
    hb = _make_hb()
    with patch.object(hb, "_ping"):
        hb.start()
        hb.stop()
        assert hb._thread is None


def test_context_manager_starts_and_stops():
    hb = _make_hb()
    ping_mock = MagicMock()
    with patch.object(hb, "_ping", ping_mock):
        with hb:
            assert hb._thread is not None
        assert hb._thread is None


# ---------------------------------------------------------------------------
# Ping behaviour
# ---------------------------------------------------------------------------

def test_ping_called_at_least_once_during_run():
    hb = _make_hb(interval=0.02)
    ping_mock = MagicMock()
    with patch.object(hb, "_ping", ping_mock):
        hb.start()
        time.sleep(0.12)
        hb.stop()
    assert ping_mock.call_count >= 1


def test_on_error_callback_invoked_on_ping_failure():
    errors = []
    hb = Heartbeat("http://127.0.0.1:1/nope", interval=0.02, on_error=errors.append)
    hb.start()
    time.sleep(0.12)
    hb.stop()
    assert len(errors) >= 1
    assert isinstance(errors[0], Exception)


def test_ping_suppresses_error_without_callback():
    hb = Heartbeat("http://127.0.0.1:1/nope", interval=0.02)
    # Should not raise even without an on_error handler.
    hb._ping()
