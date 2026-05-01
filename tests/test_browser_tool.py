"""Tests for browser tool — mocks the _BrowserSession to avoid real Chromium."""

from __future__ import annotations

from unittest.mock import MagicMock

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
