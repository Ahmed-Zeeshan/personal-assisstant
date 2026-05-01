"""Tests for browser tool — mocks the _BrowserSession to avoid real Chromium."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voice_assistant.tools.browser import (
    _BrowserSession,
    browser_click,
    browser_goto,
    browser_keyboard,
    browser_read,
    browser_type,
)


@pytest.fixture(autouse=True)
def reset_browser_singleton():
    """Reset the browser singleton between tests."""
    old = _BrowserSession._instance
    _BrowserSession._instance = None
    yield
    _BrowserSession._instance = old


def _make_mock_session(**returns):
    """Create a mock _BrowserSession with canned return values."""
    sess = MagicMock(spec=_BrowserSession)
    sess.goto.return_value = returns.get("goto", {"url": "https://example.com", "title": "Example"})
    sess.click.return_value = returns.get("click", {"ok": True})
    sess.type_text.return_value = returns.get("type_text", {"ok": True})
    sess.read.return_value = returns.get("read", {"text": "Hello world"})
    sess.keyboard_press.return_value = returns.get("keyboard_press", {"ok": True})
    sess.wait_for.return_value = returns.get("wait_for", {"ok": True})
    return sess


def test_browser_goto_calls_session(monkeypatch, tmp_path):
    mock_sess = _make_mock_session(goto={"url": "https://example.com", "title": "Example"})
    monkeypatch.setattr("voice_assistant.tools.browser._session", lambda **kw: mock_sess)
    result = browser_goto(url="https://example.com")
    assert result["url"] == "https://example.com"
    mock_sess.goto.assert_called_once_with("https://example.com")


def test_browser_click_calls_session(monkeypatch):
    mock_sess = _make_mock_session()
    monkeypatch.setattr("voice_assistant.tools.browser._session", lambda **kw: mock_sess)
    result = browser_click(selector="#submit")
    assert result["ok"] is True
    mock_sess.click.assert_called_once_with("#submit")


def test_browser_type_calls_session(monkeypatch):
    mock_sess = _make_mock_session()
    monkeypatch.setattr("voice_assistant.tools.browser._session", lambda **kw: mock_sess)
    result = browser_type(selector="#q", text="hello")
    assert result["ok"] is True
    mock_sess.type_text.assert_called_once_with("#q", "hello")


def test_browser_read_calls_session(monkeypatch):
    mock_sess = _make_mock_session(read={"text": "page content"})
    monkeypatch.setattr("voice_assistant.tools.browser._session", lambda **kw: mock_sess)
    result = browser_read(selector="main")
    assert result["text"] == "page content"
    mock_sess.read.assert_called_once_with("main")


def test_browser_keyboard_calls_session(monkeypatch):
    mock_sess = _make_mock_session()
    monkeypatch.setattr("voice_assistant.tools.browser._session", lambda **kw: mock_sess)
    result = browser_keyboard(key="Enter")
    assert result["ok"] is True
    mock_sess.keyboard_press.assert_called_once_with("Enter")


# ---- CDP attach tests --------------------------------------------------------


def _run_async(coro):
    """Run a coroutine synchronously in a temporary event loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _make_fake_pw(
    *,
    connect_raises: Exception | None = None,
    connect_returns_contexts: list | None = None,
    launch_persistent_called: list | None = None,
) -> MagicMock:
    """Build a fake Playwright object wired for CDP tests.

    Parameters
    ----------
    connect_raises:
        If set, ``connect_over_cdp`` raises this exception.
    connect_returns_contexts:
        List of context objects to return in ``browser.contexts``.
        Defaults to a single ``MagicMock()``.
    launch_persistent_called:
        Mutable list; appended to when ``launch_persistent_context`` is called.
    """
    if connect_returns_contexts is None:
        connect_returns_contexts = [MagicMock()]
    if launch_persistent_called is None:
        launch_persistent_called = []

    fake_context = MagicMock()

    async def fake_connect(url, **kw):
        if connect_raises is not None:
            raise connect_raises
        browser = MagicMock()
        browser.contexts = connect_returns_contexts
        return browser

    async def fake_launch(*a, **kw):
        launch_persistent_called.append(True)
        return fake_context

    fake_chromium = MagicMock()
    fake_chromium.connect_over_cdp = fake_connect
    fake_chromium.launch_persistent_context = fake_launch

    fake_pw = MagicMock()
    fake_pw.chromium = fake_chromium
    return fake_pw


def _make_session_with_pw(tmp_path, cdp_port=9222, fake_pw=None):
    """Create a _BrowserSession bypassing __init__, inject a pre-built fake_pw."""
    session = _BrowserSession.__new__(_BrowserSession)
    session._profile = tmp_path / "profile"
    session._headless = True
    session._cdp_port = cdp_port
    session._cdp_connected = False
    session._context = None
    session._pw = fake_pw  # injected; _setup will overwrite self._pw but chromium is already set
    return session


def test_cdp_connect_succeeds_uses_existing_context(tmp_path):
    """When connect_over_cdp succeeds, _cdp_connected=True and launch_persistent_context is NOT called."""
    lp_called: list = []
    fake_context = MagicMock()
    fp = _make_fake_pw(
        connect_returns_contexts=[fake_context],
        launch_persistent_called=lp_called,
    )

    session = _make_session_with_pw(tmp_path, cdp_port=9222, fake_pw=fp)

    with patch("playwright.async_api.async_playwright") as mock_apw:
        mock_apw.return_value.start = AsyncMock(return_value=fp)
        _run_async(session._setup())

    assert session._cdp_connected is True
    assert session._context is fake_context
    assert not lp_called, "launch_persistent_context must NOT be called on CDP success"


def test_cdp_connect_fails_falls_back_to_persistent(tmp_path):
    """When connect_over_cdp raises, launch_persistent_context IS called."""
    lp_called: list = []
    fp = _make_fake_pw(
        connect_raises=ConnectionRefusedError("port not open"),
        launch_persistent_called=lp_called,
    )

    session = _make_session_with_pw(tmp_path, cdp_port=9222, fake_pw=fp)

    with patch("playwright.async_api.async_playwright") as mock_apw:
        mock_apw.return_value.start = AsyncMock(return_value=fp)
        _run_async(session._setup())

    assert session._cdp_connected is False
    assert lp_called, "launch_persistent_context must be called as fallback"


def test_cdp_port_none_skips_cdp_attempt(tmp_path):
    """When cdp_port=None, no CDP attempt is made — goes straight to persistent profile."""
    lp_called: list = []
    connect_called: list = []

    async def fake_connect_spy(url, **kw):
        connect_called.append(True)
        return MagicMock()

    async def fake_launch(*a, **kw):
        lp_called.append(True)
        return MagicMock()

    fake_chromium = MagicMock()
    fake_chromium.connect_over_cdp = fake_connect_spy
    fake_chromium.launch_persistent_context = fake_launch
    fake_pw = MagicMock()
    fake_pw.chromium = fake_chromium

    session = _make_session_with_pw(tmp_path, cdp_port=None, fake_pw=fake_pw)

    with patch("playwright.async_api.async_playwright") as mock_apw:
        mock_apw.return_value.start = AsyncMock(return_value=fake_pw)
        _run_async(session._setup())

    assert not connect_called, "connect_over_cdp must NOT be called when cdp_port=None"
    assert lp_called
    assert session._cdp_connected is False
