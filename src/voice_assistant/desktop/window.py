from __future__ import annotations
import json
import logging
import threading
from importlib import resources
from pathlib import Path
from typing import Callable, Any

from voice_assistant.desktop.bridge import Bridge
from voice_assistant.desktop.events import EventBus

log = logging.getLogger(__name__)


def _resolve_index_html() -> str:
    """Locate the bundled web_dist/index.html via importlib.resources."""
    try:
        files = resources.files("voice_assistant") / "desktop" / "web_dist"
        index = files / "index.html"
        return str(index)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        raise RuntimeError(
            "voice-assistant desktop frontend bundle missing — please reinstall "
            "with the [desktop] extra and ensure web/dist was built before packaging."
        ) from e


class DesktopApp:
    """Opens the PyWebView window and pumps EventBus events into the page."""

    def __init__(
        self,
        *,
        bridge: Bridge,
        bus: EventBus,
        title: str = "voice-assistant",
        width: int = 800,
        height: int = 720,
    ) -> None:
        self._bridge = bridge
        self._bus = bus
        self._title = title
        self._width = width
        self._height = height
        self._window: Any | None = None
        self._unsubscribe: Callable[[], None] | None = None

    def run(self) -> None:
        try:
            import webview  # PyWebView
        except ImportError as e:
            raise RuntimeError(
                "PyWebView not installed. Run: pip install voice-assistant[desktop]"
            ) from e

        index_path = _resolve_index_html()
        self._window = webview.create_window(
            title=self._title,
            url=f"file://{index_path}",
            js_api=self._bridge,
            width=self._width,
            height=self._height,
            min_size=(720, 600),
            background_color="#0b0d10",
        )

        def _on_loaded() -> None:
            # Subscribe to the bus once the window is ready.
            self._unsubscribe = self._bus.subscribe(self._push_to_js)
            # Publish initial config so the UI populates.
            self._bus.publish({"type": "config", "cfg": self._bridge.get_config()})
            self._bus.publish({"type": "status", "value": "idle"})

        self._window.events.loaded += _on_loaded

        # Run the GUI event loop on the calling thread (must be the main thread on macOS).
        webview.start(debug=False)

        # Cleanup
        if self._unsubscribe:
            self._unsubscribe()

    def _push_to_js(self, event: dict[str, Any]) -> None:
        """Marshal an event to JS via window.va.emit().

        Called from the publisher's thread; PyWebView's evaluate_js is thread-safe.
        """
        if self._window is None:
            return
        try:
            payload = json.dumps(event)
            self._window.evaluate_js(f"window.va && window.va.emit({payload})")
        except Exception:
            log.exception("failed to push event to JS")
