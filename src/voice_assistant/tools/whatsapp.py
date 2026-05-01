"""WhatsApp send tool. Built on the Playwright browser tool.

First call: WhatsApp Web loads, you scan a QR code from the phone (one-time).
Subsequent calls: fully automatic.

Hard rate limit: 5 messages / 5 minutes — prevents accidental spam that
WhatsApp's anti-automation could ban the number for.

send_whatsapp_to_contact implements a two-step confirmation flow:
  1. Call with confirmed=False (default) → returns preview + matches, does NOT send.
  2. Call with confirmed=True → actually sends.
"""

from __future__ import annotations

import re
import time
from collections import deque
from pathlib import Path
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


# ---------------------------------------------------------------------------
# Helper: scrape search results
# ---------------------------------------------------------------------------

_SCRAPE_JS = """
(() => {
  const out = [];
  const rows = document.querySelectorAll('div[role="listitem"], div[data-testid^="cell-frame-container"]');
  for (let i = 0; i < Math.min(rows.length, 5); i++) {
    const row = rows[i];
    const nameEl = row.querySelector('span[dir="auto"][title], span[title]');
    const subtitleEls = row.querySelectorAll('span[dir="ltr"], span[dir="auto"]');
    const subtitle = subtitleEls.length > 1 ? subtitleEls[subtitleEls.length-1].textContent.trim() : '';
    if (nameEl) {
      out.push({
        index: i,
        name: nameEl.getAttribute('title') || nameEl.textContent.trim(),
        subtitle: subtitle.slice(0, 80),
      });
    }
  }
  return out;
})()
"""

_VERIFY_JS_TMPL = """
(() => {{
  const outs = document.querySelectorAll(
    'div.message-out, '
    + 'div[data-testid="msg-container"][data-direction="out"], '
    + 'div[role="row"][tabindex="-1"]'
  );
  if (!outs.length) return null;
  const last = outs[outs.length - 1];
  const txt = last.querySelector('span[dir="ltr"], span[dir="auto"]');
  return txt ? txt.textContent.trim() : null;
}})()
"""


def _scrape_search_results(sess: Any) -> list[dict[str, Any]]:
    """Return up to 5 visible chat names from current search results."""
    try:
        raw = sess.evaluate(_SCRAPE_JS)
        return raw if isinstance(raw, list) else []
    except Exception:
        return []


def _verify_last_outgoing_message(sess: Any, expected_text: str) -> bool:
    """Check that the last outgoing message bubble matches *expected_text*."""
    try:
        actual = sess.evaluate(_VERIFY_JS_TMPL)
        return bool(actual) and actual.strip() == expected_text.strip()
    except Exception:
        return False


def _capture_failure_screenshot(sess: Any, hint: str = "") -> str | None:
    """Take a screenshot and save to ~/.voice-assistant/screenshots/. Returns path or None."""
    folder = Path.home() / ".voice-assistant" / "screenshots"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"whatsapp-error-{int(time.time())}.png"
    try:
        sess.screenshot(path=path)
        return str(path)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# send_whatsapp_message (phone-based, unchanged in behaviour)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# send_whatsapp_to_contact (two-step confirmation, multi-match, verification)
# ---------------------------------------------------------------------------


def send_whatsapp_to_contact(
    *,
    name: str,
    message: str,
    confirmed: bool = False,
    match_index: int = 0,
) -> dict[str, Any]:
    """Send a WhatsApp message to a contact found by name via WhatsApp Web search.

    Two-step flow
    -------------
    Call 1 — confirmed=False (default):
        Opens WhatsApp Web, searches for *name*, scrapes up to 5 matches from
        the results list, and returns a preview dict WITHOUT sending.

        Returns::

            {
              "preview": "Send 'hello' to <name>?",
              "matches": [{"index": 0, "name": "...", "subtitle": "..."}, ...],
              "confirmation_required": True,
            }

    Call 2 — confirmed=True:
        Re-runs the search, clicks the result at *match_index*, types *message*,
        clicks send, waits 1.5 s, reads the last outgoing bubble to verify, and
        records the send against the rate limit.

        Returns::

            {"ok": True, "contact": "<name>", "verified": True|False, ...}

    Parameters
    ----------
    name:
        Contact name to search for in WhatsApp.
    message:
        Message text, ≤1000 chars.
    confirmed:
        False (default) → preview only, no message sent.
        True → actually send.
    match_index:
        0-based index into the matches list returned by the preview call.
        Defaults to 0 (first result).
    """
    if not name.strip():
        raise ValueError("contact name required")
    if not message.strip() or len(message) > 1000:
        raise ValueError("message empty or > 1000 chars")

    # Rate limit is only checked (and recorded) on actual sends.
    if confirmed:
        _check_rate_limit()

    sess = _session()

    # ------------------------------------------------------------------
    # Step 1: Navigate to WhatsApp Web
    # ------------------------------------------------------------------
    try:
        sess.goto("https://web.whatsapp.com/")
    except RuntimeError as exc:
        screenshot = _capture_failure_screenshot(sess, "goto failed")
        suffix = f" Screenshot: {screenshot}" if screenshot else ""
        raise RuntimeError(f"Failed to open WhatsApp Web.{suffix}") from exc

    # ------------------------------------------------------------------
    # Step 2: Wait for logged-in state
    # ------------------------------------------------------------------
    try:
        sess.wait_for(
            'div[contenteditable="true"][data-tab="3"], '
            'div[role="textbox"][contenteditable="true"], '
            'header[data-testid="chatlist-header"]',
            timeout_ms=30000,
        )
    except Exception as exc:
        screenshot = _capture_failure_screenshot(sess, "login check")
        suffix = f" Screenshot: {screenshot}" if screenshot else ""
        raise RuntimeError(
            "WhatsApp Web didn't load. If this is your first send, you may need "
            f"to scan the QR code in the launched browser.{suffix}"
        ) from exc

    # ------------------------------------------------------------------
    # Step 3: Search for the contact
    # ------------------------------------------------------------------
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
        except Exception:  # noqa: S112
            continue
    if not searched:
        screenshot = _capture_failure_screenshot(sess, "search box")
        suffix = f" Screenshot: {screenshot}" if screenshot else ""
        raise RuntimeError(f"couldn't find WhatsApp Web search box.{suffix}")

    # ------------------------------------------------------------------
    # Step 4: Wait for results to appear
    # ------------------------------------------------------------------
    try:
        sess.wait_for(
            'div[role="listitem"], div[data-testid^="cell-frame-container"]',
            timeout_ms=10000,
        )
    except Exception as exc:
        screenshot = _capture_failure_screenshot(sess, "search results")
        suffix = f" Screenshot: {screenshot}" if screenshot else ""
        raise RuntimeError(f"no results found for {name!r}.{suffix}") from exc

    # ------------------------------------------------------------------
    # Step 5: Scrape matches (always done — used for preview AND confirmed)
    # ------------------------------------------------------------------
    matches = _scrape_search_results(sess)

    # ------------------------------------------------------------------
    # Preview mode — return without sending
    # ------------------------------------------------------------------
    if not confirmed:
        preview_name = matches[0]["name"] if matches else name
        return {
            "preview": f"Send '{message}' to {preview_name}?",
            "matches": matches,
            "confirmation_required": True,
        }

    # ------------------------------------------------------------------
    # Confirmed mode — click the chosen result
    # ------------------------------------------------------------------
    # Clamp match_index to valid range
    safe_index = max(0, min(match_index, max(len(matches) - 1, 0)))

    # Build a list of selectors to try, preferring the nth element.
    result_selectors = [
        f'div[role="listitem"]:nth-of-type({safe_index + 1})',
        f'div[data-testid^="cell-frame-container"]:nth-of-type({safe_index + 1})',
        'div[role="listitem"]:first-of-type',
        'div[data-testid^="cell-frame-container"]:first-of-type',
        'div[role="listitem"]',
    ]
    clicked_result = False
    for sel in result_selectors:
        try:
            sess.click(sel)
            clicked_result = True
            break
        except Exception:  # noqa: S112
            continue
    if not clicked_result:
        screenshot = _capture_failure_screenshot(sess, "click result")
        suffix = f" Screenshot: {screenshot}" if screenshot else ""
        raise RuntimeError(f"could not click search result at index {match_index}.{suffix}")

    # ------------------------------------------------------------------
    # Step 6: Click compose box and type
    # ------------------------------------------------------------------
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
        except Exception:  # noqa: S112
            continue
    if not typed:
        screenshot = _capture_failure_screenshot(sess, "compose box")
        suffix = f" Screenshot: {screenshot}" if screenshot else ""
        raise RuntimeError(f"couldn't find WhatsApp Web message composer.{suffix}")

    # ------------------------------------------------------------------
    # Step 7: Send
    # ------------------------------------------------------------------
    send_via: str = "button"
    for sel in ('[data-testid="send"]', 'button[aria-label="Send"]', 'span[data-icon="send"]'):
        try:
            sess.click(sel)
            break
        except Exception:  # noqa: S112
            continue
    else:
        # Last-ditch: Enter key
        try:
            sess.keyboard_press("Enter")
            send_via = "enter-key"
        except Exception as exc:
            screenshot = _capture_failure_screenshot(sess, "send button")
            suffix = f" Screenshot: {screenshot}" if screenshot else ""
            raise RuntimeError(f"failed to send: {exc}.{suffix}") from exc

    # ------------------------------------------------------------------
    # Step 8: Record send against rate limit
    # ------------------------------------------------------------------
    _recent_sends.append(time.time())

    # ------------------------------------------------------------------
    # Step 9: Post-send verification (wait briefly then check last bubble)
    # ------------------------------------------------------------------
    time.sleep(1.5)
    verified = _verify_last_outgoing_message(sess, message)

    result: dict[str, Any] = {
        "ok": True,
        "contact": name,
        "verified": verified,
    }
    if send_via == "enter-key":
        result["via"] = "enter-key"
    if not verified:
        result["warning"] = (
            "Could not verify the message appeared in the chat. "
            "Check WhatsApp Web manually."
        )
    return result


# ---------------------------------------------------------------------------
# JSON schemas for the LLM
# ---------------------------------------------------------------------------

WHATSAPP_CONTACT_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "send_whatsapp_to_contact",
        "description": (
            "Send a WhatsApp message via WhatsApp Web by contact NAME. "
            "ALWAYS call first with confirmed=False to get a preview and list of matches. "
            "Show the user which contact will be sent to and the message text, ask 'confirm?', "
            "then call again with confirmed=True (and match_index from the preview) to send. "
            "This two-step pattern prevents sending to the wrong person. "
            "Rate-limited 5/5min."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Contact name to search for in WhatsApp."},
                "message": {"type": "string", "description": "Message text, ≤1000 chars."},
                "confirmed": {
                    "type": "boolean",
                    "description": "False for preview (default), True to actually send.",
                    "default": False,
                },
                "match_index": {
                    "type": "integer",
                    "description": "Index of the chosen match from the preview list (0-based, default 0).",
                    "default": 0,
                },
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
