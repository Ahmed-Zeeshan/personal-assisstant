from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

log = logging.getLogger(__name__)


class EventBus:
    """Pub-sub bus with per-event-type throttling.

    Used between the orchestrator/audio threads (publishers) and the
    PyWebView GUI thread (subscriber that pushes to JS).
    """

    _AUDIO_LEVEL_INTERVAL_S = 1 / 30  # 30 Hz

    def __init__(self) -> None:
        self._subscribers: list[Callable[[dict[str, Any]], None]] = []
        self._last_audio_level_at: float = 0.0

    def subscribe(self, fn: Callable[[dict[str, Any]], None]) -> Callable[[], None]:
        self._subscribers.append(fn)

        def _unsub() -> None:
            try:
                self._subscribers.remove(fn)
            except ValueError:
                pass

        return _unsub

    def publish(self, event: dict[str, Any]) -> None:
        if event.get("type") == "audio_level":
            now = time.monotonic()
            if now - self._last_audio_level_at < self._AUDIO_LEVEL_INTERVAL_S:
                return
            self._last_audio_level_at = now
        for fn in list(self._subscribers):
            try:
                fn(event)
            except Exception:  # subscriber failure must not crash the bus
                log.debug("event subscriber raised", exc_info=True)
