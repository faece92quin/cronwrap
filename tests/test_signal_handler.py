"""Tests for cronwrap.signal_handler."""

import signal
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.signal_handler import SignalHandler, make_signal_handler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_handler(*callbacks):
    h = SignalHandler()
    for cb in callbacks:
        h.register(cb)
    return h


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_initial_state_not_interrupted():
    h = SignalHandler()
    assert h.triggered is None
    assert h.was_interrupted is False


def test_register_adds_callback():
    cb = MagicMock()
    h = _make_handler(cb)
    assert cb in h._callbacks


def test_handle_invokes_callbacks():
    cb1 = MagicMock()
    cb2 = MagicMock()
    h = _make_handler(cb1, cb2)
    h._handle(signal.SIGTERM, None)
    cb1.assert_called_once_with(signal.SIGTERM)
    cb2.assert_called_once_with(signal.SIGTERM)


def test_handle_sets_triggered():
    h = SignalHandler()
    h._handle(signal.SIGINT, None)
    assert h.triggered == signal.SIGINT
    assert h.was_interrupted is True


def test_handle_continues_despite_callback_error():
    bad_cb = MagicMock(side_effect=RuntimeError("boom"))
    good_cb = MagicMock()
    h = _make_handler(bad_cb, good_cb)
    h._handle(signal.SIGTERM, None)  # should not raise
    good_cb.assert_called_once_with(signal.SIGTERM)


def test_install_and_restore():
    h = SignalHandler()
    original = signal.getsignal(signal.SIGTERM)
    h.install([signal.SIGTERM])
    assert signal.getsignal(signal.SIGTERM) == h._handle
    h.restore()
    assert signal.getsignal(signal.SIGTERM) == original
    assert h._original == {}


def test_make_signal_handler_installs_and_registers():
    cb = MagicMock()
    original_term = signal.getsignal(signal.SIGTERM)
    original_int = signal.getsignal(signal.SIGINT)
    try:
        h = make_signal_handler(callbacks=[cb])
        assert cb in h._callbacks
        assert signal.getsignal(signal.SIGTERM) == h._handle
        assert signal.getsignal(signal.SIGINT) == h._handle
    finally:
        signal.signal(signal.SIGTERM, original_term)
        signal.signal(signal.SIGINT, original_int)


def test_make_signal_handler_custom_signals():
    original = signal.getsignal(signal.SIGUSR1)
    try:
        h = make_signal_handler(signals=[signal.SIGUSR1])
        assert signal.getsignal(signal.SIGUSR1) == h._handle
        h.restore()
    finally:
        signal.signal(signal.SIGUSR1, original)
