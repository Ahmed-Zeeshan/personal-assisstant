"""WhatsApp send tool. Built on the Playwright browser tool.

First call: WhatsApp Web loads, you scan a QR code from the phone (one-time).
Subsequent calls: fully automatic.

Hard rate limit: 5 messages / 5 minutes — prevents accidental spam that
WhatsApp's anti-automation could ban the number for.
"""

from __future__ import annotations

import re
import time
from collections import deque
from typing import Any
from urllib.parse import quote

from voice_assistant.tools.browser import _session

_RATE_LIMIT_WINDOW_S = 300
_RATE_LIMIT_COUNT = 5
_recent_sends: deque[float] = deque()


def _check_rate_limit() -> None:
    now = time.time()
    while _recent_sends and _recent_sends[0] < now - _RATE_LIMIT_WINDOW_S:
        _recent_sends.popleft()
    if len(_recent_sends) >= _RATE_LIMIT_COUNT:
        raise RuntimeError(
            f"WhatsApp rate limit hit: max {_RATE_LIMIT_COUNT} messages "
            f"per {_RATE_LIMIT_WINDOW_S // 60} minutes. Wait and retry."
        )


def _normalize_phone(phone: str) -> str:
    """Accept '+44 7700 900000' or '447700900000' or '07700900000'.

    Returns the digits only; the URL handler doesn't need '+'.
    """
    digits = re.sub(r"\D", "", phone)
    if not digits:
        raise ValueError(f"phone has no digits: {phone!r}")
    return digits


def send_whatsapp_message(*, phone: str, message: str) -> dict[str, Any]:
    """Send a WhatsApp message to a phone number via WhatsApp Web.

    Args:
        phone: International phone number with country code. Examples:
               '+923001234567', '923001234567', '00923001234567'.
        message: The message text. Max ~1000 chars (WhatsApp's limit).

    Returns:
        {"ok": True, "phone": <normalized>} on success.

    Raises:
        RuntimeError: if rate-limited, or WhatsApp Web isn't logged in.
        ValueError: invalid phone or empty message.
    """
    if not message.strip():
        raise ValueError("message cannot be empty")
    if len(message) > 1000:
        raise ValueError("WhatsApp messages capped at ~1000 characters")
    digits = _normalize_phone(phone)
    _check_rate_limit()

    sess = _session()

    # Step 1: open the chat. wa.me redirects to web.whatsapp.com/send/?phone=…&text=…
    url = f"https://web.whatsapp.com/send?phone={digits}&text={quote(message)}"
    sess.goto(url)

    # Step 2: wait for the chat to load — WhatsApp Web shows a "Continue to Chat" button
    # the first time, otherwise it goes straight to the message composer.
    # We wait for the send button (data-testid="send" or aria-label="Send").
    send_selector = '[data-testid="send"], button[aria-label="Send"], span[data-icon="send"]'
    try:
        sess.wait_for(send_selector, timeout_ms=30000)
    except Exception as exc:
        raise RuntimeError(
            "WhatsApp Web didn't load the chat. Likely cause: not logged in. "
            "Run send_whatsapp_message once interactively to scan the QR code."
        ) from exc

    # Step 3: click send (multiple selectors as fallback because WhatsApp's DOM changes).
    for sel in ('[data-testid="send"]', 'button[aria-label="Send"]', 'span[data-icon="send"]'):
        try:
            sess.click(sel)
            _recent_sends.append(time.time())
            return {"ok": True, "phone": digits}
        except Exception:  # noqa: S112
            continue

    # Last-ditch: hit Enter in the composer
    try:
        sess.keyboard_press("Enter")
        _recent_sends.append(time.time())
        return {"ok": True, "phone": digits, "via": "enter-key"}
    except Exception as exc:
        raise RuntimeError(f"failed to click send button: {exc}") from exc


def send_whatsapp_to_contact(*, name: str, message: str) -> dict[str, Any]:
    """Send a WhatsApp message to a contact found by name via WhatsApp Web search.

    Steps:
      1. Open https://web.whatsapp.com (persistent profile preserves login)
      2. Click the search box (data-testid="chat-list-search")
      3. Type the contact name
      4. Click the first result (matching exact or close-name)
      5. Click the message composer
      6. Type the message
      7. Click the send button
    """
    if not name.strip():
        raise ValueError("contact name required")
    if not message.strip() or len(message) > 1000:
        raise ValueError("message empty or > 1000 chars")
    _check_rate_limit()

    sess = _session()
    sess.goto("https://web.whatsapp.com/")

    # Wait for WhatsApp Web to load (logged-in state)
    try:
        sess.wait_for(
            'div[contenteditable="true"][data-tab="3"], '
            'div[role="textbox"][contenteditable="true"], '
            'header[data-testid="chatlist-header"]',
            timeout_ms=30000,
        )
    except Exception as exc:
        raise RuntimeError(
            "WhatsApp Web didn't load. If this is your first send, you may need "
            "to scan the QR code in the launched browser."
        ) from exc

    # Search for the contact
    search_selectors = [
        'div[contenteditable="true"][data-tab="3"]',
        'div[role="textbox"][title*="Search"]',
        'div[contenteditable="true"]:not([data-tab="10"])',
    ]
    searched = False
    for sel in search_selectors:
        try:
            sess.click(sel)
            sess.type_text(sel, name)
            searched = True
            break
        except Exception:
            continue
    if not searched:
        raise RuntimeError("couldn't find WhatsApp Web search box")

    # Wait for results, click the first chat-row
    try:
        sess.wait_for(
            'div[role="listitem"], div[data-testid^="cell-frame-container"]',
            timeout_ms=10000,
        )
    except Exception as exc:
        raise RuntimeError(f"no results found for {name!r}") from exc

    for sel in (
        'div[role="listitem"]:first-of-type',
        'div[data-testid^="cell-frame-container"]:first-of-type',
        'div[role="listitem"]',
    ):
        try:
            sess.click(sel)
            break
        except Exception:
            continue

    # Click compose box and type
    compose_selectors = [
        'div[contenteditable="true"][data-tab="10"]',
        'div[role="textbox"][contenteditable="true"][data-tab="10"]',
        'footer div[contenteditable="true"]',
    ]
    typed = False
    for sel in compose_selectors:
        try:
            sess.click(sel)
            sess.type_text(sel, message)
            typed = True
            break
        except Exception:
            continue
    if not typed:
        raise RuntimeError("couldn't find WhatsApp Web message composer")

    # Send
    for sel in ('[data-testid="send"]', 'button[aria-label="Send"]', 'span[data-icon="send"]'):
        try:
            sess.click(sel)
            _recent_sends.append(time.time())
            return {"ok": True, "contact": name}
        except Exception:
            continue
    try:
        sess.keyboard_press("Enter")
        _recent_sends.append(time.time())
        return {"ok": True, "contact": name, "via": "enter-key"}
    except Exception as exc:
        raise RuntimeError(f"failed to send: {exc}") from exc


WHATSAPP_CONTACT_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "send_whatsapp_to_contact",
        "description": (
            "Send a WhatsApp message to a contact found by NAME (e.g. 'Arslan', 'Mom'). "
            "Searches WhatsApp Web for the name and sends to the first matching chat. "
            "Use this when the user gives a name; use send_whatsapp_message when they give a phone number. "
            "Rate-limited to 5/5min."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Contact name as it appears in WhatsApp"},
                "message": {"type": "string", "description": "Message text, ≤1000 chars"},
            },
            "required": ["name", "message"],
            "additionalProperties": False,
        },
    },
}


WHATSAPP_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "send_whatsapp_message",
        "description": (
            "Send a WhatsApp message to a phone number via WhatsApp Web. "
            "Phone must include the country code (e.g. +923001234567). "
            "First use requires the user to scan a QR code in the launched browser; "
            "subsequent sends are automatic. Rate-limited to 5/5min to avoid bans."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "Phone number with country code."},
                "message": {"type": "string", "description": "Message text, ≤1000 chars."},
            },
            "required": ["phone", "message"],
            "additionalProperties": False,
        },
    },
}
