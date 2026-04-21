"""Heartbeat support: emit periodic signals to a URL while a job runs."""

import threading
import time
from typing import Callable, Optional

import urllib.request
import urllib.error


class Heartbeat:
    """Sends HTTP GET requests to a URL at a fixed interval in a background thread."""

    def __init__(
        self,
        url: str,
        interval: float = 30.0,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        self.url = url
        self.interval = interval
        self.on_error = on_error
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the background heartbeat thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the heartbeat thread to stop and wait for it."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval + 5)
            self._thread = None

    def _loop(self) -> None:
        while not self._stop_event.wait(timeout=self.interval):
            self._ping()

    def _ping(self) -> None:
        try:
            with urllib.request.urlopen(self.url, timeout=10):  # noqa: S310
                pass
        except Exception as exc:  # noqa: BLE001
            if self.on_error is not None:
                self.on_error(exc)

    def __enter__(self) -> "Heartbeat":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()


def make_heartbeat(
    url: Optional[str],
    interval: float = 30.0,
    on_error: Optional[Callable[[Exception], None]] = None,
) -> Optional[Heartbeat]:
    """Return a Heartbeat if *url* is non-empty, otherwise None."""
    if not url:
        return None
    return Heartbeat(url, interval=interval, on_error=on_error)
