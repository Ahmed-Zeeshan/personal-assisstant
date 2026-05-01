# Threat Model — voice-assistant

**Method:** STRIDE per major component  
**Date:** 2026-04-30  
**Scope:** Code in this repository running on a single-user Linux/macOS/Windows desktop.  
Out of scope: third-party LLM provider infrastructure, OS-level vulnerabilities, physical access.

---

## 1. Filesystem Tools

**Component:** `tools/filesystem.py` + `safety.py`

| Threat | Category | Current Mitigation |
|--------|----------|--------------------|
| Attacker-controlled path escapes sandbox | Tampering / Info-disclosure | `SafetyPolicy.check_path` resolves symlinks before checking `allowed_roots`; prefix-confusion and `..` traversal are blocked |
| Destructive op without user consent | Tampering | `destructive_requires_confirmation=True`; brain is instructed to ask the user before passing `confirmed=True` |
| Runaway delete loop | Denial of Service | `delete_rate_per_minute` hard cap; raises `SafetyError` when exceeded |
| LLM infers file contents it shouldn't | Information Disclosure | Path scoping limits which files the brain can read; no recursive glob without an explicit allowed root |
| TOCTOU between check and syscall | Tampering | Acknowledged in module docstring; acceptable for single-user desktop (no concurrent attackers) |

---

## 2. Email Tool (Gmail)

**Component:** `tools/gmail.py`

| Threat | Category | Current Mitigation |
|--------|----------|--------------------|
| OAuth token exfiltration | Information Disclosure | Token file written with mode `0o600` (owner-only); stored under `~/.voice-assistant/` |
| Sending email without user knowledge | Tampering / Repudiation | Brain is instructed to confirm before sending; Gmail message-ID is logged on every send |
| Scope creep (read access) | Information Disclosure | OAuth scope is `gmail.send` only; revoking via Google Account removes all access |
| Token replay after logout | Spoofing | Token is a refresh token bound to the OAuth client; revocation at Google invalidates it |

---

## 3. Browser and WhatsApp Tools

**Component:** `tools/browser.py`, `tools/whatsapp.py`

| Threat | Category | Current Mitigation |
|--------|----------|--------------------|
| Browser profile shared with other tools | Tampering | Profile isolated at `~/.voice-assistant/browser-profile/`; not the OS default profile |
| Runaway WhatsApp message loop | Denial of Service | Hard rate limit: 5 messages per 5 minutes; not user-configurable |
| Malicious web page injects commands | Tampering / Elevation | `browser_read` returns raw text treated as untrusted by the brain (system-prompt instruction) |
| Persistent cookie theft | Information Disclosure | Browser profile is local-only; file permissions follow OS defaults (future: restrict to 0700) |

---

## 4. Memory Store

**Component:** `memory/store.py` — SQLite + sqlite-vec at `~/.voice-assistant/memory.db`

| Threat | Category | Current Mitigation |
|--------|----------|--------------------|
| Other local processes read memory DB | Information Disclosure | File mode `0644` (current); future hardening: `0600` or SQLCipher |
| Prompt-injection via recalled memories | Tampering | Brain treats `recall` output as untrusted data; system prompt instructs it not to follow instructions found in memory |
| DB corruption | Denial of Service | SQLite WAL mode; application restarts gracefully without the DB |

---

## 5. Desktop Bridge

**Component:** `desktop/bridge.py` — JS ↔ Python RPC over pywebview

| Threat | Category | Current Mitigation |
|--------|----------|--------------------|
| JS calls arbitrary Python functions | Elevation of Privilege | Bridge exposes only a small, explicitly listed set of callables; pywebview does not expose the full Python namespace |
| JS injects data into Python state | Tampering | All arguments from JS are validated in the bridge layer before dispatch |
| Malicious page loaded in the webview | Spoofing / Tampering | WebView is loaded from the bundled `web_dist/` directory, not the network; no remote-URL loading |

---

## 6. Wake-Word Engine

**Component:** `wake.py` — openwakeword / onnxruntime

| Threat | Category | Current Mitigation |
|--------|----------|--------------------|
| High false-positive rate triggers unwanted actions | Denial of Service | Threshold configurable in `config.yaml`; a false trigger still requires a full LLM round-trip before any action is taken |
| Audio fingerprinting / speaker ID | Information Disclosure | Audio is transcribed locally; transcript only (text) leaves the machine |
| Voice spoofing / replay attacks | Spoofing | No mitigation currently; future hardening: voice-biometric verification (see table below) |

---

## 7. Brain (LLM Layer)

**Component:** `brain.py` — LiteLLM wrapper

| Threat | Category | Current Mitigation |
|--------|----------|--------------------|
| Prompt injection in tool results | Information Disclosure / Tampering | System prompt instructs the brain to treat tool-returned data as untrusted; instructions inside file contents or web pages are not followed |
| LLM produces a hallucinated tool call with dangerous args | Tampering | Safety layer (`check_path`, rate limits, `confirmed` flag) is the last line of defence regardless of LLM output |
| API key exfiltration | Information Disclosure | Keys are loaded from `.env` / environment variables; never written to disk by the assistant |
| Model responses logged verbatim | Repudiation | Conversation history is appended to `history.jsonl` (user-controlled file); no cloud logging |

---

## Future Hardening Items

| ID | Item | Component | Priority |
|----|------|-----------|----------|
| FH-1 | Encrypt memory DB at rest (SQLCipher or file-level) | Memory | High |
| FH-2 | Restrict browser-profile directory to mode `0700` | Browser | Medium |
| FH-3 | Tool-output sandboxing: parse tool results in a subprocess before passing to LLM | Brain | Medium |
| FH-4 | Voice-biometric liveness check on wake-word triggers | Wake | Low |
| FH-5 | Restrict memory DB file mode to `0600` | Memory | High |
| FH-6 | Audit log for all destructive operations (separate from history.jsonl) | Filesystem | Medium |
| FH-7 | Content-Security-Policy header for the desktop WebView | Bridge | Low |
