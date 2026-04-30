"""Tests for the WhatsApp send tool.

All browser interactions are mocked — no real Chromium or network needed.
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from voice_assistant.tools.whatsapp import (
    _check_rate_limit,
    _normalize_phone,
    _recent_sends,
    send_whatsapp_message,
)


@pytest.fixture(autouse=True)
def clear_rate_limit():
    """Reset the rate-limit deque between tests."""
    _recent_sends.clear()
    yield
    _recent_sends.clear()


def _make_mock_session(*, wait_raises: Exception | None = None, click_raises: bool = False):
    sess = MagicMock()
    sess.goto.return_value = {"url": "https://web.whatsapp.com/send?phone=441234567890"}
    if wait_raises is not None:
        sess.wait_for.side_effect = wait_raises
    else:
        sess.wait_for.return_value = {"ok": True}
    if click_raises:
        sess.click.side_effect = Exception("element not found")
    else:
        sess.click.return_value = {"ok": True}
    sess.keyboard_press.return_value = {"ok": True}
    return sess


# ---- _normalize_phone --------------------------------------------------------


def test_normalize_strips_formatting():
    assert _normalize_phone("+44 7700 900000") == "447700900000"


def test_normalize_preserves_pure_digits():
    assert _normalize_phone("923001234567") == "923001234567"


def test_normalize_empty_raises():
    with pytest.raises(ValueError, match="no digits"):
        _normalize_phone("no-digits-here")


# ---- _check_rate_limit -------------------------------------------------------


def test_rate_limit_allows_up_to_max():
    for _ in range(5):
        _check_rate_limit()
        _recent_sends.append(time.time())
    # 6th call should raise
    with pytest.raises(RuntimeError, match="rate limit"):
        _check_rate_limit()


def test_rate_limit_expires_old_entries():
    # Insert 5 fake sends in the distant past
    old_ts = time.time() - 400  # outside the 300s window
    for _ in range(5):
        _recent_sends.append(old_ts)
    # Should not raise — all old entries are purged
    _check_rate_limit()


# ---- send_whatsapp_message ---------------------------------------------------


def test_send_happy_path(monkeypatch):
    mock_sess = _make_mock_session()
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: mock_sess)

    result = send_whatsapp_message(phone="+44 7700 900000", message="Hello!")

    assert result["ok"] is True
    assert result["phone"] == "447700900000"
    # URL must contain the phone digits
    url_arg = mock_sess.goto.call_args[0][0]
    assert "447700900000" in url_arg
    assert "Hello" in url_arg


def test_send_url_encodes_message(monkeypatch):
    mock_sess = _make_mock_session()
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: mock_sess)

    send_whatsapp_message(phone="923001234567", message="Hi there & welcome!")

    url_arg = mock_sess.goto.call_args[0][0]
    assert "Hi+there" in url_arg or "Hi%20there" in url_arg or "Hi there" not in url_arg


def test_send_empty_message_raises(monkeypatch):
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: _make_mock_session())
    with pytest.raises(ValueError, match="empty"):
        send_whatsapp_message(phone="+1234567890", message="   ")


def test_send_too_long_message_raises(monkeypatch):
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: _make_mock_session())
    with pytest.raises(ValueError, match="1000"):
        send_whatsapp_message(phone="+1234567890", message="x" * 1001)


def test_send_not_logged_in_raises(monkeypatch):
    mock_sess = _make_mock_session(wait_raises=Exception("timeout"))
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: mock_sess)

    with pytest.raises(RuntimeError, match="not logged in"):
        send_whatsapp_message(phone="+923001234567", message="Hello")


def test_send_click_fallback_to_enter(monkeypatch):
    """If all CSS-selector clicks fail, the tool falls back to keyboard Enter."""
    mock_sess = _make_mock_session(click_raises=True)
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: mock_sess)

    result = send_whatsapp_message(phone="+923001234567", message="Hello")

    assert result["ok"] is True
    assert result.get("via") == "enter-key"
    mock_sess.keyboard_press.assert_called_once_with("Enter")


def test_send_increments_rate_limit(monkeypatch):
    mock_sess = _make_mock_session()
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: mock_sess)

    assert len(_recent_sends) == 0
    send_whatsapp_message(phone="+923001234567", message="Hello")
    assert len(_recent_sends) == 1


def test_send_rate_limited_after_5(monkeypatch):
    mock_sess = _make_mock_session()
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: mock_sess)

    for _ in range(5):
        send_whatsapp_message(phone="+923001234567", message="Hello")

    with pytest.raises(RuntimeError, match="rate limit"):
        send_whatsapp_message(phone="+923001234567", message="Hello")
