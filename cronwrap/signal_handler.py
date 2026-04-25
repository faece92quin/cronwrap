"""Graceful signal handling for cron job processes."""

import os
import signal
import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SignalHandler:
    """Registers and manages OS signal callbacks for graceful shutdown."""

    _callbacks: List[Callable[[int], None]] = field(default_factory=list)
    _triggered: Optional[int] = field(default=None, init=False)
    _original: dict = field(default_factory=dict, init=False)

    def register(self, callback: Callable[[int], None]) -> None:
        """Add a callback to invoke when a handled signal is received."""
        self._callbacks.append(callback)

    def install(self, signals: Optional[List[int]] = None) -> None:
        """Install signal handlers for the given signal numbers.

        Defaults to SIGTERM and SIGINT if *signals* is not provided.
        """
        if signals is None:
            signals = [signal.SIGTERM, signal.SIGINT]
        for sig in signals:
            self._original[sig] = signal.signal(sig, self._handle)
            logger.debug("Installed handler for signal %s", sig)

    def restore(self) -> None:
        """Restore original signal handlers."""
        for sig, handler in self._original.items():
            signal.signal(sig, handler)
            logger.debug("Restored original handler for signal %s", sig)
        self._original.clear()

    def _handle(self, signum: int, _frame) -> None:  # type: ignore[type-arg]
        logger.warning("Received signal %s — running shutdown callbacks", signum)
        self._triggered = signum
        for cb in self._callbacks:
            try:
                cb(signum)
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Signal callback raised: %s", exc)

    @property
    def triggered(self) -> Optional[int]:
        """Return the signal number that was received, or None."""
        return self._triggered

    @property
    def was_interrupted(self) -> bool:
        """True if any handled signal was received."""
        return self._triggered is not None


def make_signal_handler(
    signals: Optional[List[int]] = None,
    callbacks: Optional[List[Callable[[int], None]]] = None,
) -> SignalHandler:
    """Create and install a SignalHandler in one call."""
    handler = SignalHandler()
    for cb in callbacks or []:
        handler.register(cb)
    handler.install(signals)
    return handler
