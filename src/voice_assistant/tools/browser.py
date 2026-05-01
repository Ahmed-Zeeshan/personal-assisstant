"""Browser automation tool — Playwright with a persistent profile.

The first call launches Chromium with a profile dir at
~/.voice-assistant/browser-profile/. Subsequent calls reuse it (so logins
persist).

CDP attach mode: when VA_CHROME_CDP_PORT is set (or cdp_port is passed),
_BrowserSession first tries to connect to an existing Chrome instance via
the Chrome DevTools Protocol. If that succeeds, the user's real Chrome tabs
(and cookies) are available. If it fails, the session silently falls back to
launching its own isolated Chromium.

Public API is sync; Playwright's async loop is hidden behind a worker
thread + asyncio.run_coroutine_threadsafe.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from pathlib import Path
from typing import Any, cast

log = logging.getLogger(__name__)

# Default CDP port Chrome listens on when launched with --remote-debugging-port
_DEFAULT_CDP_PORT = 9222


def _cdp_port_from_env() -> int | None:
    """Return the CDP port from VA_CHROME_CDP_PORT, or None if unset/invalid."""
    raw = os.environ.get("VA_CHROME_CDP_PORT", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        log.warning("VA_CHROME_CDP_PORT=%r is not a valid port number; ignoring", raw)
        return None


class _BrowserSession:
    """Singleton-ish: one persistent Chromium per process."""

    _lock = threading.Lock()
    _instance: _BrowserSession | None = None

    def __init__(
        self,
        profile_dir: Path,
        headless: bool,
        cdp_port: int | None = _DEFAULT_CDP_PORT,
    ) -> None:
        self._profile = profile_dir
        self._headless = headless
        # Environment variable overrides the constructor argument.
        env_port = _cdp_port_from_env()
        self._cdp_port: int | None = env_port if env_port is not None else cdp_port
        self._cdp_connected: bool = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._context: Any = None  # playwright BrowserContext
        self._ready = threading.Event()
        self._start_thread()

    # ---- public property -----------------------------------------------------

    @property
    def is_cdp_connected(self) -> bool:
        """True when the session is attached to an existing Chrome via CDP."""
        return self._cdp_connected

    def _start_thread(self) -> None:
        def run() -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._setup())
            self._ready.set()
            self._loop.run_forever()

        self._thread = threading.Thread(target=run, name="va-browser", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=30)

    async def _setup(self) -> None:
        from playwright.async_api import async_playwright

        self._pw = await async_playwright().start()

        # --- Try CDP attach first (if a port is configured) ------------------
        if self._cdp_port is not None:
            try:
                browser = await asyncio.wait_for(
                    self._pw.chromium.connect_over_cdp(
                        f"http://localhost:{self._cdp_port}"
                    ),
                    timeout=2.0,
                )
                self._context = (
                    browser.contexts[0]
                    if browser.contexts
                    else await browser.new_context()
                )
                self._cdp_connected = True
                log.info(
                    "attached to existing Chrome via CDP on port %d", self._cdp_port
                )
                return
            except Exception as exc:
                log.debug(
                    "CDP attach to port %d failed: %s — falling back to isolated profile",
                    self._cdp_port,
                    exc,
                )

        # --- Fall back: launch isolated Chromium with persistent profile ------
        self._profile.mkdir(parents=True, exist_ok=True)
        self._context = await self._pw.chromium.launch_persistent_context(
            user_data_dir=str(self._profile),
            headless=self._headless,
            viewport={"width": 1280, "height": 800},
        )
        self._cdp_connected = False

    def _run(self, coro: Any) -> Any:
        assert self._loop is not None
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=60)

    @classmethod
    def get(
        cls,
        *,
        profile_dir: Path,
        headless: bool = False,
        cdp_port: int | None = _DEFAULT_CDP_PORT,
    ) -> _BrowserSession:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(profile_dir, headless, cdp_port=cdp_port)
            return cls._instance

    async def _page(self) -> Any:
        assert self._context is not None
        if self._context.pages:
            return self._context.pages[-1]
        return await self._context.new_page()

    # ---- public sync facade --------------------------------------------------

    def find_or_open_page(
        self, url_substring: str, *, fallback_url: str
    ) -> dict[str, Any]:
        """Find an open tab whose URL contains *url_substring*; if none, open *fallback_url*.

        Returns ``{"existing": True, "url": <tab url>}`` when an existing tab is
        found and brought to the foreground, or ``{"existing": False, "url":
        fallback_url}`` when a new tab had to be opened.

        Subsequent calls to :meth:`goto` / :meth:`click` / etc. operate on the
        page that is now at the front of ``context.pages``.
        """

        async def _find() -> dict[str, Any]:
            assert self._context is not None
            for page in self._context.pages:
                if url_substring in (page.url or ""):
                    await page.bring_to_front()
                    return {"existing": True, "url": page.url}
            # No matching tab — open a new one.
            new_page = await self._page()
            await new_page.goto(
                fallback_url, wait_until="domcontentloaded", timeout=20000
            )
            return {"existing": False, "url": new_page.url}

        return cast(dict[str, Any], self._run(_find()))

    def goto(self, url: str) -> dict[str, Any]:
        async def _go() -> dict[str, Any]:
            page = await self._page()
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            return {"url": page.url, "title": await page.title()}

        return cast(dict[str, Any], self._run(_go()))

    def click(self, selector: str) -> dict[str, Any]:
        async def _click() -> dict[str, Any]:
            page = await self._page()
            await page.click(selector, timeout=10000)
            return {"ok": True}

        return cast(dict[str, Any], self._run(_click()))

    def type_text(self, selector: str, text: str) -> dict[str, Any]:
        async def _type() -> dict[str, Any]:
            page = await self._page()
            await page.fill(selector, text, timeout=10000)
            return {"ok": True}

        return cast(dict[str, Any], self._run(_type()))

    def read(self, selector: str = "body") -> dict[str, Any]:
        async def _read() -> dict[str, Any]:
            page = await self._page()
            text = await page.inner_text(selector, timeout=10000)
            return {"text": text[:8000]}

        return cast(dict[str, Any], self._run(_read()))

    def screenshot(self, *, path: Path) -> dict[str, Any]:
        async def _shot() -> dict[str, Any]:
            page = await self._page()
            await page.screenshot(path=str(path), type="png")
            return {"path": str(path)}

        return cast(dict[str, Any], self._run(_shot()))

    def keyboard_press(self, key: str) -> dict[str, Any]:
        async def _press() -> dict[str, Any]:
            page = await self._page()
            await page.keyboard.press(key)
            return {"ok": True}

        return cast(dict[str, Any], self._run(_press()))

    def wait_for(self, selector: str, *, timeout_ms: int = 10000) -> dict[str, Any]:
        async def _wait() -> dict[str, Any]:
            page = await self._page()
            await page.wait_for_selector(selector, timeout=timeout_ms)
            return {"ok": True}

        return cast(dict[str, Any], self._run(_wait()))

    def evaluate(self, js: str) -> Any:
        """Evaluate a JavaScript expression in the current page and return the result."""

        async def _eval() -> Any:
            page = await self._page()
            return await page.evaluate(js)

        return self._run(_eval())


def _session(profile_dir: Path | None = None) -> _BrowserSession:
    return _BrowserSession.get(
        profile_dir=profile_dir or Path.home() / ".voice-assistant" / "browser-profile",
    )


# ---- tool functions exposed to the LLM --------------------------------------


def browser_goto(*, url: str) -> dict[str, Any]:
    """Open a URL in the persistent browser."""
    return _session().goto(url)


def browser_click(*, selector: str) -> dict[str, Any]:
    """Click an element by CSS selector."""
    return _session().click(selector)


def browser_type(*, selector: str, text: str) -> dict[str, Any]:
    """Fill a text field by CSS selector."""
    return _session().type_text(selector, text)


def browser_read(*, selector: str = "body") -> dict[str, Any]:
    """Read visible text from an element (default: entire body)."""
    return _session().read(selector)


def browser_keyboard(*, key: str) -> dict[str, Any]:
    """Press a keyboard key (e.g. 'Enter', 'Escape', 'Tab')."""
    return _session().keyboard_press(key)


BROWSER_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "browser_goto",
            "description": "Navigate the browser to a URL.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "Absolute http(s) URL."}},
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": "Click a page element by CSS selector.",
            "parameters": {
                "type": "object",
                "properties": {"selector": {"type": "string"}},
                "required": ["selector"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_type",
            "description": "Fill a text field by CSS selector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["selector", "text"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_read",
            "description": "Read visible text from a page element (default: body).",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "default": "body"},
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_keyboard",
            "description": "Press a keyboard key in the browser.",
            "parameters": {
                "type": "object",
                "properties": {"key": {"type": "string", "description": "Key name, e.g. 'Enter'."}},
                "required": ["key"],
                "additionalProperties": False,
            },
        },
    },
]
