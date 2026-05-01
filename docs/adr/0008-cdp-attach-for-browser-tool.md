# 0008 — Chrome DevTools Protocol attach for the browser tool

**Status:** Accepted  
**Date:** 2026-04-30

## Context

The browser tool (`tools/browser.py`) always launched an isolated Chromium
instance with a persistent profile at `~/.voice-assistant/browser-profile/`.
This worked for headless automation but created a friction point for users
who wanted to use tools that depend on their real browser session (e.g.
WhatsApp Web, where they are already logged in, or sites behind SSO).

The user's regular Chrome and the assistant's Chromium are completely separate
processes with separate cookie stores. When a user said "send a WhatsApp to
Alice", the assistant's browser would open a fresh WhatsApp Web session,
requiring a QR-code scan.

## Decision

Extend `_BrowserSession` to attempt a Chrome DevTools Protocol (CDP) attach
before falling back to launching its own Chromium.

On start-up:

1. Read `VA_CHROME_CDP_PORT` (default `9222`).
2. Call `playwright.chromium.connect_over_cdp(f"http://localhost:{port}")` with
   a 2-second timeout.
3. If it succeeds, store `_cdp_connected = True` and use the first existing
   context (or create one) — the user's real tabs are now accessible.
4. If it fails for any reason, log a DEBUG message and launch the isolated
   persistent profile as before (`launch_persistent_context`). The user sees
   no error.

`WhatsApp.send_whatsapp_to_contact` is updated to call
`sess.find_or_open_page("web.whatsapp.com", fallback_url=...)` instead of
unconditionally navigating. When an existing tab is found and we are
CDP-connected, the login wait-for timeout is reduced from 30 s to 5 s (the
user is almost certainly already logged in).

Error messages distinguish the two failure modes:

- Not CDP-connected: suggest `--remote-debugging-port=9222`.
- CDP-connected but no WhatsApp tab found: tell the user to open
  `web.whatsapp.com` in Chrome.

A lightweight probe (`Bridge.is_browser_attached_to_chrome`) uses `httpx` to
`GET /json/version` (1-second timeout) without launching any browser — safe
to call from the Settings drawer on open.

## Consequences

- **Zero-config**: users who never launch Chrome with a debug port experience
  no change.
- **Low latency**: the CDP probe has a hard 2-second timeout; GUI startup is
  not blocked.
- **Security**: CDP grants full control of the attached browser. Users opt in
  explicitly by launching Chrome with `--remote-debugging-port`. The assistant
  never enables the debug port itself.
- **WhatsApp UX**: users with WhatsApp Web open in Chrome can send messages
  without a QR scan.
- **Testability**: `_cdp_connected` is a public property; tests can assert on
  it without starting a real browser.
