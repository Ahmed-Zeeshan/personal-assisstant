# Speed + system context + WhatsApp-by-name plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development.

**Goal:** Five fixes from a real user smoke test:

1. **`send_whatsapp_to_contact(name, message)`** — composite tool that uses browser primitives to navigate web.whatsapp.com, search for the contact, click the first result, type, send.
2. **System context** — new `get_system_info()` tool + auto-inject OS/host/timezone/locale into the system prompt every call so the assistant knows where it's installed.
3. **TTS speed parameter** — `tts.speed: float = 1.15` default. OpenAI TTS supports it natively; Piper supports `length_scale`. Settings slider in Voice tab.
4. **Brain system prompt: WhatsApp routing examples** — make it use the right tool path explicitly.
5. **STT pre-warm on app start** — load Whisper in a background thread during GUI init so the first voice press doesn't pay 1-2s model-load.

---

## Task 1: System context tool + auto-injection

**Files:**
- Create: `src/voice_assistant/tools/system_info.py`
- Modify: `src/voice_assistant/tools/__init__.py` — register
- Modify: `src/voice_assistant/brain.py` — auto-inject context block at top of system prompt
- Create: `tests/test_system_info.py`

```python
# src/voice_assistant/tools/system_info.py
"""Tool that returns the running machine's context: OS, time, locale, etc."""
from __future__ import annotations
import locale as _locale
import platform
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


def get_system_info() -> dict[str, Any]:
    """Return basic info about the machine the assistant is running on."""
    try:
        tz_name = datetime.now().astimezone().tzinfo.tzname(None) or "UTC"
    except Exception:
        tz_name = "UTC"
    try:
        loc, _ = _locale.getlocale()
    except Exception:
        loc = None
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "machine_arch": platform.machine(),
        "hostname": socket.gethostname(),
        "user_home": str(Path.home()),
        "current_time_iso": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "timezone": tz_name,
        "locale": loc or "C",
        "python_version": platform.python_version(),
    }


SYSTEM_INFO_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_system_info",
        "description": "Return facts about the host machine (OS, hostname, time, timezone, locale). Use when the user asks about their computer, current time, where they are, etc.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
}


def system_context_block() -> str:
    """One-line system-prompt block summarising the host. Cheap, no I/O."""
    info = get_system_info()
    return (
        f"Host: {info['hostname']} ({info['os']} {info['machine_arch']}). "
        f"Time: {info['current_time_iso']}. Timezone: {info['timezone']}. "
        f"Locale: {info['locale']}. Home: {info['user_home']}."
    )
```

In `brain.py` `_build_system_prompt`:

```python
from voice_assistant.tools.system_info import system_context_block

def _build_system_prompt(user: UserConfig | None) -> str:
    context = system_context_block()
    # ... existing language_line + address_line ...
    return (
        f"You are voice-assistant — a personal desktop helper that talks to the user by voice.\n"
        f"Machine context: {context}\n"
        f"{language_line}"
        # ... rest unchanged
    )
```

Tests in `tests/test_system_info.py`:
- `get_system_info()` returns expected keys
- `system_context_block()` is non-empty and contains hostname

Commit: `feat(tools): system_info tool + auto-injected machine context`

---

## Task 2: TTS speed parameter

**Files:**
- Modify: `src/voice_assistant/config.py` — `TTSConfig.speed: float = 1.15`
- Modify: `src/voice_assistant/setup_wizard.py` — add `tts_speed` to WizardAnswers + render
- Modify: `src/voice_assistant/tts/openai_engine.py` — pass `speed=` to API
- Modify: `src/voice_assistant/tts/piper_engine.py` — `length_scale` (Piper inverts: speed=1.5 means length_scale=1/1.5)
- Modify: `src/voice_assistant/tts/__init__.py` — `make_speaker(voice_id=, speed=)`
- Modify: `src/voice_assistant/cli.py` — pass `speed=cfg.tts.speed`
- Modify: `web/src/components/Settings.ts` — slider in Voice tab
- Modify: `src/voice_assistant/desktop/bridge.py` — round-trip

Settings slider: 0.75 / 1.0 / 1.15 (default) / 1.3 / 1.5. Native input range step 0.05.

Validate `0.5 <= speed <= 2.0` in pydantic.

Commit: `feat(tts): configurable speech speed (default 1.15 — natural-fast)`

---

## Task 3: STT pre-warm on app start

**Files:**
- Modify: `src/voice_assistant/cli.py` — start Transcriber load in a background thread

```python
# In _run_gui_mode, after the existing transcriber init:
def _prewarm_transcriber() -> None:
    """Load the whisper model in the background so the first hotkey press is fast."""
    if transcriber is not None:
        try:
            # Force model load by calling a tiny no-op transcribe
            import numpy as np
            silence = np.zeros(16000, dtype=np.float32).tobytes()
            transcriber.transcribe(silence)
            log.info("STT pre-warmed")
        except Exception as exc:
            log.debug("STT pre-warm failed (non-fatal): %s", exc)

threading.Thread(target=_prewarm_transcriber, daemon=True).start()
```

Commit: `feat(stt): pre-warm Whisper model on GUI startup`

---

## Task 4: `send_whatsapp_to_contact(name, message)` — browser-based

**Files:**
- Modify: `src/voice_assistant/tools/whatsapp.py` — add a second tool function
- Modify: `src/voice_assistant/tools/__init__.py` — register `send_whatsapp_to_contact`
- Add tests covering the new tool with mocked browser session

```python
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
        sess.wait_for('div[role="listitem"], div[data-testid^="cell-frame-container"]', timeout_ms=10000)
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


WHATSAPP_CONTACT_SCHEMA = {
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
                "name":    {"type": "string", "description": "Contact name as it appears in WhatsApp"},
                "message": {"type": "string", "description": "Message text, ≤1000 chars"},
            },
            "required": ["name", "message"],
            "additionalProperties": False,
        },
    },
}
```

Tests with mocked `_session()` covering: name normalization, rate limit shared with phone-based sender, fallback selectors.

Commit: `feat(tools): send_whatsapp_to_contact (browser-based, contact-name search)`

---

## Task 5: Brain system-prompt examples for tool routing

**Files:**
- Modify: `src/voice_assistant/brain.py` — sharpen `_build_system_prompt`

Add a "Tool routing" guidance block after the existing rules:

```python
"\nTool routing:\n"
"- 'send WhatsApp to <NAME>' → use send_whatsapp_to_contact(name, message)\n"
"- 'send WhatsApp to <PHONE>' (digits/+) → use send_whatsapp_message(phone, message)\n"
"- 'open <URL>' → use open_url(url)\n"
"- 'search the web for X' → use web_search; then web_fetch the most relevant result\n"
"- 'what time is it / what OS am I on / where am I' → use get_system_info\n"
"- 'remember that X' / 'my Y is Z' → use remember(fact)\n"
"- 'what's my Y' / 'do you know Z' → use recall(query)\n"
"Don't ask the user for the phone if they gave you a name — use the contact tool. "
"Don't describe the action; perform it.\n"
```

Commit: `feat(brain): explicit tool-routing examples in system prompt`

---

## Task 6: Verify + push

- pytest, ruff, mypy clean
- web bundle rebuilt
- Reinstall editable, restart GUI
- Push to main

---

## Done criteria

- "Send a WhatsApp to Arslan saying 'where are you?'" → no longer asks for phone; navigates WhatsApp Web → searches "Arslan" → clicks first result → sends.
- "What's my OS?" → uses `get_system_info`, replies with hostname + OS.
- TTS speed slider in Settings affects voice playback rate; default 1.15 (natural-fast).
- First hotkey press after GUI launch responds <500ms (Whisper pre-warmed).
- All ~244 tests pass.
