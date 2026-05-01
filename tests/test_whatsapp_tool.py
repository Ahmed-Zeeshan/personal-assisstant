"""Tests for the WhatsApp send tool.

All browser interactions are mocked — no real Chromium or network needed.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from voice_assistant.tools.whatsapp import (
    _check_rate_limit,
    _normalize_phone,
    _recent_sends,
    send_whatsapp_message,
    send_whatsapp_to_contact,
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


# ---- send_whatsapp_to_contact -----------------------------------------------


def _make_contact_session(
    *,
    wait_raises: Exception | None = None,
    click_raises: bool = False,
    type_text_raises: bool = False,
    evaluate_return: list | None = None,
    cdp_connected: bool = False,
    existing_tab: bool = False,
) -> MagicMock:
    """Mock session for contact-based WhatsApp sends."""
    sess = MagicMock()
    # find_or_open_page replaces the old direct goto() call.
    sess.find_or_open_page.return_value = {
        "existing": existing_tab,
        "url": "https://web.whatsapp.com/",
    }
    sess.goto.return_value = {"url": "https://web.whatsapp.com/"}
    # is_cdp_connected is a property on the real class; expose it as an attribute
    # on the mock so the whatsapp code can read it.
    type(sess).is_cdp_connected = property(lambda self: cdp_connected)
    if wait_raises is not None:
        sess.wait_for.side_effect = wait_raises
    else:
        sess.wait_for.return_value = {"ok": True}
    if click_raises:
        sess.click.side_effect = Exception("element not found")
    else:
        sess.click.return_value = {"ok": True}
    if type_text_raises:
        sess.type_text.side_effect = Exception("not found")
    else:
        sess.type_text.return_value = {"ok": True}
    sess.keyboard_press.return_value = {"ok": True}
    sess.screenshot.return_value = {"path": "/tmp/whatsapp-error.png"}
    # Default: evaluate returns a single match
    if evaluate_return is None:
        sess.evaluate.return_value = [
            {"index": 0, "name": "Arslan Khan", "subtitle": "Hey!"}
        ]
    else:
        sess.evaluate.return_value = evaluate_return
    return sess


# --- existing tests (updated to pass confirmed=True for actual sends) ---------


def test_contact_send_happy_path(monkeypatch):
    mock_sess = _make_contact_session()
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: mock_sess)
    # Verify message so verified=True
    mock_sess.evaluate.side_effect = [
        [{"index": 0, "name": "Arslan Khan", "subtitle": ""}],  # scrape call
        "where are you?",                                         # verify call
    ]

    with patch("voice_assistant.tools.whatsapp.time") as mock_time:
        mock_time.time.return_value = 1000.0
        mock_time.sleep = lambda _: None
        result = send_whatsapp_to_contact(name="Arslan", message="where are you?", confirmed=True)

    assert result["ok"] is True
    assert result["contact"] == "Arslan"
    # find_or_open_page must have been called to navigate to WhatsApp Web
    mock_sess.find_or_open_page.assert_called_once_with(
        "web.whatsapp.com", fallback_url="https://web.whatsapp.com/"
    )


def test_contact_send_order_of_operations(monkeypatch):
    """Verify: find_or_open_page → wait_for → click search → type_text → … → compose → send."""
    call_log: list[str] = []
    sess = MagicMock()
    sess.find_or_open_page.side_effect = lambda *a, **kw: (
        call_log.append("find_or_open_page") or {"existing": False, "url": "https://web.whatsapp.com/"}
    )
    type(sess).is_cdp_connected = property(lambda self: False)
    sess.wait_for.side_effect = lambda *a, **kw: call_log.append("wait_for") or {"ok": True}
    sess.click.side_effect = lambda *a, **kw: call_log.append("click") or {"ok": True}
    sess.type_text.side_effect = lambda *a, **kw: call_log.append("type_text") or {"ok": True}
    sess.keyboard_press.side_effect = lambda *a, **kw: call_log.append("keyboard_press") or {
        "ok": True
    }
    sess.evaluate.return_value = [{"index": 0, "name": "Mom", "subtitle": ""}]
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    with patch("voice_assistant.tools.whatsapp.time") as mock_time:
        mock_time.time.return_value = 1000.0
        mock_time.sleep = lambda _: None
        send_whatsapp_to_contact(name="Mom", message="Hi!", confirmed=True)

    # find_or_open_page is first
    assert call_log[0] == "find_or_open_page"
    # wait_for appears before type_text (page load check)
    assert call_log.index("wait_for") < call_log.index("type_text")
    # type_text (search box fill) happens before final send step
    assert "type_text" in call_log


def test_contact_send_empty_name_raises(monkeypatch):
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: _make_contact_session())
    with pytest.raises(ValueError, match="contact name required"):
        send_whatsapp_to_contact(name="   ", message="Hi!")


def test_contact_send_empty_message_raises(monkeypatch):
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: _make_contact_session())
    with pytest.raises(ValueError, match="message empty or > 1000 chars"):
        send_whatsapp_to_contact(name="Arslan", message="   ")


def test_contact_send_too_long_message_raises(monkeypatch):
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: _make_contact_session())
    with pytest.raises(ValueError, match="1000"):
        send_whatsapp_to_contact(name="Arslan", message="x" * 1001)


def test_contact_send_not_logged_in_raises(monkeypatch):
    mock_sess = _make_contact_session(wait_raises=Exception("timeout"))
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: mock_sess)

    with pytest.raises(RuntimeError, match="QR code"):
        send_whatsapp_to_contact(name="Arslan", message="Hello")


def test_contact_send_shares_rate_limit_with_phone_sender(monkeypatch):
    """Rate limit deque is shared: 5 phone sends should block contact send."""
    mock_sess = _make_mock_session()
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: mock_sess)

    for _ in range(5):
        send_whatsapp_message(phone="+923001234567", message="Hello")

    with pytest.raises(RuntimeError, match="rate limit"):
        send_whatsapp_to_contact(name="Arslan", message="Hi", confirmed=True)


def test_contact_send_increments_rate_limit(monkeypatch):
    mock_sess = _make_contact_session()
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: mock_sess)

    assert len(_recent_sends) == 0
    with patch("voice_assistant.tools.whatsapp.time") as mock_time:
        mock_time.time.return_value = 1000.0
        mock_time.sleep = lambda _: None
        send_whatsapp_to_contact(name="Arslan", message="Hello", confirmed=True)
    assert len(_recent_sends) == 1


def test_contact_send_fallback_to_enter_on_click_fail(monkeypatch):
    """If all send-button CSS selectors fail, fall back to keyboard Enter."""
    sess = _make_contact_session()
    # make click fail only for the send button selectors (last click calls)
    click_call_count = [0]

    def selective_click(sel: str) -> dict:
        click_call_count[0] += 1
        # Fail specifically on the send-button selectors
        if any(s in sel for s in ['data-testid="send"', 'aria-label="Send"', 'data-icon="send"']):
            raise Exception("send button not found")
        return {"ok": True}

    sess.click.side_effect = selective_click
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    with patch("voice_assistant.tools.whatsapp.time") as mock_time:
        mock_time.time.return_value = 1000.0
        mock_time.sleep = lambda _: None
        result = send_whatsapp_to_contact(name="Arslan", message="Hello", confirmed=True)

    assert result["ok"] is True
    assert result.get("via") == "enter-key"
    sess.keyboard_press.assert_called_once_with("Enter")


# ---- NEW: two-step confirmation tests ----------------------------------------


def test_send_whatsapp_to_contact_unconfirmed_returns_preview_does_not_send(monkeypatch):
    """confirmed=False: navigate+search+scrape but NO compose or send actions."""
    sess = _make_contact_session(
        evaluate_return=[
            {"index": 0, "name": "Arslan Khan", "subtitle": "Hey"},
            {"index": 1, "name": "Arslan Ali", "subtitle": ""},
        ]
    )
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    result = send_whatsapp_to_contact(name="Arslan", message="where are you?", confirmed=False)

    # Must return preview structure
    assert result["confirmation_required"] is True
    assert "preview" in result
    assert "matches" in result
    assert len(result["matches"]) == 2
    assert result["matches"][0]["name"] == "Arslan Khan"

    # find_or_open_page must have been called to navigate to WhatsApp Web
    sess.find_or_open_page.assert_called_once_with(
        "web.whatsapp.com", fallback_url="https://web.whatsapp.com/"
    )
    # type_text should have been called (for search box)
    sess.type_text.assert_called()

    # But the compose box should NOT have been typed into — i.e. type_text should
    # only have been called for the search (name), never with the message content.
    type_text_calls = [c.args[1] for c in sess.type_text.call_args_list if c.args]
    assert "where are you?" not in type_text_calls

    # keyboard_press (Enter/send) must NOT have been called
    sess.keyboard_press.assert_not_called()

    # Rate limit must NOT have been incremented
    assert len(_recent_sends) == 0


def test_send_whatsapp_to_contact_confirmed_sends_and_verifies(monkeypatch):
    """confirmed=True: full path; verify returns True when text matches."""
    sess = _make_contact_session()
    # First evaluate call = scrape, second = verify
    sess.evaluate.side_effect = [
        [{"index": 0, "name": "Arslan Khan", "subtitle": ""}],
        "where are you?",
    ]
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    with patch("voice_assistant.tools.whatsapp.time") as mock_time:
        mock_time.time.return_value = 1000.0
        mock_time.sleep = lambda _: None
        result = send_whatsapp_to_contact(
            name="Arslan", message="where are you?", confirmed=True, match_index=0
        )

    assert result["ok"] is True
    assert result["verified"] is True
    assert "warning" not in result
    # Rate limit incremented
    assert len(_recent_sends) == 1


def test_send_whatsapp_to_contact_with_match_index_clicks_correct_result(monkeypatch):
    """match_index=2 → the nth-of-type(3) selector is tried first."""
    sess = _make_contact_session(
        evaluate_return=[
            {"index": 0, "name": "A", "subtitle": ""},
            {"index": 1, "name": "B", "subtitle": ""},
            {"index": 2, "name": "C", "subtitle": ""},
        ]
    )
    clicked_selectors: list[str] = []

    def record_click(sel: str):
        clicked_selectors.append(sel)
        return {"ok": True}

    sess.click.side_effect = record_click
    # second evaluate = verify
    sess.evaluate.side_effect = [
        [{"index": 0, "name": "A"}, {"index": 1, "name": "B"}, {"index": 2, "name": "C"}],
        None,  # verify returns None → verified=False
    ]
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    with patch("voice_assistant.tools.whatsapp.time") as mock_time:
        mock_time.time.return_value = 1000.0
        mock_time.sleep = lambda _: None
        result = send_whatsapp_to_contact(
            name="X", message="hello", confirmed=True, match_index=2
        )

    assert result["ok"] is True
    # The nth-of-type(3) selector must appear among the clicked selectors
    assert any("nth-of-type(3)" in s for s in clicked_selectors)


def test_send_whatsapp_to_contact_failure_captures_screenshot(monkeypatch):
    """On click failure, the RuntimeError message includes the screenshot path."""
    sess = _make_contact_session()
    # Make scrape succeed, but type_text fail on compose box → triggers compose error path
    sess.evaluate.return_value = [{"index": 0, "name": "Arslan Khan", "subtitle": ""}]
    # Allow search clicks to succeed but fail on compose box
    compose_selectors = {
        'div[contenteditable="true"][data-tab="10"]',
        'div[role="textbox"][contenteditable="true"][data-tab="10"]',
        'footer div[contenteditable="true"]',
    }

    def selective_type(sel: str, text: str):
        if sel in compose_selectors:
            raise Exception("compose not found")
        return {"ok": True}

    sess.type_text.side_effect = selective_type
    sess.screenshot.return_value = {"path": "/home/user/.voice-assistant/screenshots/whatsapp-error-1000.png"}
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    with patch("voice_assistant.tools.whatsapp.time") as mock_time:
        mock_time.time.return_value = 1000.0
        mock_time.sleep = lambda _: None
        with pytest.raises(RuntimeError) as exc_info:
            send_whatsapp_to_contact(name="Arslan", message="Hello", confirmed=True)

    # screenshot path should be in the error message
    error_msg = str(exc_info.value)
    assert "Screenshot" in error_msg or "whatsapp-error" in error_msg or ".png" in error_msg


def test_send_whatsapp_to_contact_verification_mismatch_returns_warning(monkeypatch):
    """If verify returns False, response includes verified=False and a warning."""
    sess = _make_contact_session()
    sess.evaluate.side_effect = [
        [{"index": 0, "name": "Arslan Khan", "subtitle": ""}],
        "completely different text",  # mismatch → verified=False
    ]
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    with patch("voice_assistant.tools.whatsapp.time") as mock_time:
        mock_time.time.return_value = 1000.0
        mock_time.sleep = lambda _: None
        result = send_whatsapp_to_contact(name="Arslan", message="hello", confirmed=True)

    assert result["ok"] is True
    assert result["verified"] is False
    assert "warning" in result


def test_unconfirmed_does_not_count_against_rate_limit(monkeypatch):
    """Preview calls do NOT consume rate-limit slots."""
    sess = _make_contact_session()
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    # Call preview 5 times — should not exhaust rate limit
    for _ in range(5):
        send_whatsapp_to_contact(name="Arslan", message="hi", confirmed=False)

    assert len(_recent_sends) == 0

    # A confirmed send should still be allowed
    sess.evaluate.side_effect = [
        [{"index": 0, "name": "Arslan Khan", "subtitle": ""}],
        "hi",
    ]
    with patch("voice_assistant.tools.whatsapp.time") as mock_time:
        mock_time.time.return_value = 1000.0
        mock_time.sleep = lambda _: None
        result = send_whatsapp_to_contact(name="Arslan", message="hi", confirmed=True)

    assert result["ok"] is True


def test_preview_contact_name_uses_first_match(monkeypatch):
    """Preview's 'preview' string uses the first match's resolved name."""
    sess = _make_contact_session(
        evaluate_return=[
            {"index": 0, "name": "Arslan Khan", "subtitle": "Last seen today"},
        ]
    )
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    result = send_whatsapp_to_contact(name="Arslan", message="hi!", confirmed=False)

    assert "Arslan Khan" in result["preview"]
    assert "hi!" in result["preview"]


def test_preview_falls_back_to_search_term_when_no_matches(monkeypatch):
    """Preview uses the raw search name when evaluate returns empty list."""
    sess = _make_contact_session(evaluate_return=[])
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    result = send_whatsapp_to_contact(name="Unknown Person", message="test", confirmed=False)

    assert result["confirmation_required"] is True
    assert "Unknown Person" in result["preview"]


# ---- CDP / existing-tab tests ------------------------------------------------


def test_send_whatsapp_to_contact_reuses_existing_whatsapp_tab(monkeypatch):
    """When find_or_open_page returns existing=True, the tool reuses the tab.

    In this path wait_for should be called with the SHORT (5 s) timeout
    because the user is already logged in via CDP.
    """
    sess = _make_contact_session(cdp_connected=True, existing_tab=True)
    sess.evaluate.side_effect = [
        [{"index": 0, "name": "Arslan Khan", "subtitle": ""}],
        "hello",
    ]
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    with patch("voice_assistant.tools.whatsapp.time") as mock_time:
        mock_time.time.return_value = 1000.0
        mock_time.sleep = lambda _: None
        result = send_whatsapp_to_contact(name="Arslan", message="hello", confirmed=True)

    assert result["ok"] is True

    # find_or_open_page must have been called (not goto directly)
    sess.find_or_open_page.assert_called_once_with(
        "web.whatsapp.com", fallback_url="https://web.whatsapp.com/"
    )

    # wait_for must have been called with the short 5 s (5000 ms) timeout
    wait_calls = sess.wait_for.call_args_list
    assert wait_calls, "wait_for should have been called"
    first_wait_timeout = wait_calls[0].kwargs.get("timeout_ms") or wait_calls[0].args[1]
    assert first_wait_timeout == 5000, (
        f"expected 5000 ms login timeout for existing tab; got {first_wait_timeout}"
    )


def test_send_whatsapp_no_cdp_uses_long_timeout(monkeypatch):
    """Without CDP, the login wait_for uses the full 30 s timeout."""
    sess = _make_contact_session(cdp_connected=False, existing_tab=False)
    sess.evaluate.side_effect = [
        [{"index": 0, "name": "Arslan Khan", "subtitle": ""}],
        "hi",
    ]
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    with patch("voice_assistant.tools.whatsapp.time") as mock_time:
        mock_time.time.return_value = 1000.0
        mock_time.sleep = lambda _: None
        result = send_whatsapp_to_contact(name="Arslan", message="hi", confirmed=True)

    assert result["ok"] is True

    wait_calls = sess.wait_for.call_args_list
    first_wait_timeout = wait_calls[0].kwargs.get("timeout_ms") or wait_calls[0].args[1]
    assert first_wait_timeout == 30000, (
        f"expected 30000 ms login timeout for non-CDP path; got {first_wait_timeout}"
    )


def test_login_timeout_error_message_no_cdp(monkeypatch):
    """Non-CDP login timeout → error message mentions --remote-debugging-port=9222."""
    sess = _make_contact_session(cdp_connected=False, wait_raises=Exception("timeout"))
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    with pytest.raises(RuntimeError) as exc_info:
        send_whatsapp_to_contact(name="Arslan", message="Hello")

    msg = str(exc_info.value)
    assert "--remote-debugging-port=9222" in msg
    assert "QR code" in msg


def test_login_timeout_error_message_cdp_no_tab(monkeypatch):
    """CDP-connected but no WhatsApp tab → error message tells user to open tab."""
    sess = _make_contact_session(cdp_connected=True, existing_tab=False, wait_raises=Exception("timeout"))
    monkeypatch.setattr("voice_assistant.tools.whatsapp._session", lambda: sess)

    with pytest.raises(RuntimeError) as exc_info:
        send_whatsapp_to_contact(name="Arslan", message="Hello")

    msg = str(exc_info.value)
    assert "web.whatsapp.com" in msg
    assert "Chrome tab" in msg
