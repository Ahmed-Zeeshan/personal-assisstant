# 0006 — Hard Rate Limit on send_whatsapp_message

**Status:** Accepted  
**Date:** 2026-04-30

## Context

`send_whatsapp_message` drives a real Chromium browser session to send messages
via WhatsApp Web. An uncontrolled LLM in an agentic loop could send hundreds of
messages to contacts in seconds — a privacy and trust disaster with no easy undo.

## Decision

Apply a **hard rate limit of 5 messages per 5 minutes** enforced inside
`tools/whatsapp.py` using a module-level `deque` timestamp window. The limit is
not configurable by the user to prevent accidental removal.

## Consequences

- Runaway agentic loops are capped at 5 messages before the tool starts raising
  `RuntimeError`, which the brain surfaces to the user.
- Legitimate interactive use (asking the assistant to send 1–2 messages) is
  unaffected.
- The limit applies per process; restarting the assistant resets the window.
