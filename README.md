# voice-assistant

A personal voice-controlled desktop assistant. Press a hotkey, speak, and the
assistant performs actions on your computer — file operations, sending email,
opening apps and URLs — and replies in voice.

## Status

Phase 1 — personal-tool MVP. Single user. Runs from the terminal.

## Features

- Voice in via global hotkey (default `ctrl+shift+space`)
- Local speech-to-text via faster-whisper (no audio leaves the machine)
- Pluggable LLM brain via LiteLLM: Anthropic Claude, OpenAI GPT, Google Gemini, or local Ollama
- Local text-to-speech via Piper
- Tools the brain can call:
  - `create_folder` / `create_file` / `list_folder` / `read_file` / `move_path` / `delete_path`
  - `open_url` / `open_app`
  - `send_email` (Gmail OAuth, optional)
- Safety layer: path-scoped filesystem access, destructive-op confirmation, delete rate limit

## Quickstart

```bash
git clone <this repo>
cd voice-assistant
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[audio,gmail,dev]"

cp config.yaml.example config.yaml
cp .env.example .env

# Edit .env — set ONE of:
#   ANTHROPIC_API_KEY=sk-ant-...
#   OPENAI_API_KEY=sk-...
#   GEMINI_API_KEY=...
# Edit config.yaml — set brain.provider to match.
```

Run in **text mode** (no microphone needed):

```bash
voice-assistant --text
```

Run in **voice mode**:

```bash
voice-assistant
```

Then press the configured hotkey, speak a command, and listen for the reply.

## Configuration

`config.yaml` controls everything tunable. The example file documents every
option. Highlights:

- `brain.provider` — `anthropic`, `openai`, `gemini`, or `ollama`
- `brain.model` — the model id (e.g. `claude-sonnet-4-6`, `gpt-4o`, `gemini-1.5-pro`)
- `safety.allowed_roots` — list of directories the assistant may touch
  (filesystem tools refuse anything outside this list)
- `audio.hotkey` — global trigger (e.g. `ctrl+shift+space`, `ctrl+f1`)
- `tts.voice` — Piper voice name (e.g. `en_US-amy-medium`); auto-downloaded on first use

## Gmail (optional)

If you want the assistant to send email:

1. Follow Google's [Gmail API Python quickstart](https://developers.google.com/gmail/api/quickstart/python)
   to download an OAuth `credentials.json`.
2. Place it at the path in `config.yaml -> gmail.credentials_file`
   (default: `~/.voice-assistant/gmail-creds.json`).
3. The first `send_email` call will open a browser for one-time authorisation.
4. The cached token (`oauth-token.json`) is written next to the credentials
   file with mode `0o600` (owner-only).

The OAuth scope requested is `gmail.send` only — read access is not granted.

## Safety model

- **Path scoping:** filesystem tools refuse paths outside `safety.allowed_roots`.
  Symlink escapes, `..` traversal, and prefix-confusion attacks are blocked.
- **Destructive operations** (`delete_path`, overwriting files, replacing
  existing destinations) require an explicit `confirmed=true` from the brain.
  The system prompt instructs the brain to ask the user before these.
- **Rate limit:** at most `safety.delete_rate_per_minute` deletes per minute.
- **Prompt injection defence:** the brain is told to treat tool-returned data
  (file contents, emails) as untrusted — instructions found inside that data
  are not executed.

## Tests

```bash
pytest -q
```

The test suite is 159+ tests covering safety, tools, brain wiring, orchestrator,
config, logging, audio capture, STT, TTS, Gmail, memory store, browser tool,
WhatsApp tool, and history (mocked where hardware is needed).

## Architecture

See `docs/superpowers/specs/2026-04-29-voice-assistant-design.md` for the
design and `docs/superpowers/plans/2026-04-29-voice-assistant-implementation.md`
for the implementation plan.

Modules:

- `audio_input` — hotkey listener + microphone capture with silence detection
- `stt` — faster-whisper wrapper
- `brain` — pluggable LLM via LiteLLM, returns either `PlainText` or `ToolCall`
- `tools/` — filesystem, gmail, system tools, with a registry exposing
  OpenAI-compatible JSON schemas
- `safety` — path scoping, destructive-op gating, rate limiting
- `tts` — Piper voice synthesis (local, free)
- `app` — orchestrator that wires brain → tool → brain (summary) per turn
- `cli` — argparse entry point with text and voice modes

## Tools

The assistant can invoke the following tools automatically during a conversation:

| Tool | Extra | Description |
|------|-------|-------------|
| `create_folder`, `create_file`, `read_file`, `list_folder`, `move_path`, `delete_path` | core | Filesystem operations within `safety.allowed_roots` |
| `open_url` | core | Open a URL in the system browser |
| `open_app` | core | Launch a desktop application by command name |
| `send_email` | gmail | Send a plain-text email via Gmail OAuth |
| `web_search`, `web_fetch` | web | Search the web and fetch pages |
| `remember`, `recall` | memory | Persist and retrieve facts across sessions (sqlite-vec embeddings) |
| `browser_goto`, `browser_click`, `browser_type`, `browser_read`, `browser_keyboard` | browser | Playwright-backed Chromium automation with a persistent profile |
| `send_whatsapp_message` | browser | Send a WhatsApp message via WhatsApp Web (rate-limited to 5/5 min) |

### Memory

The `[memory]` extra stores facts in `~/.voice-assistant/memory.db` using
SQLite + sqlite-vec. Ask the assistant to "remember that my work email is X"
and it will store a vector embedding. Later, "what's my work email" retrieves
the closest match automatically.

### Browser & WhatsApp

The `[browser]` extra can work in two modes:

**Default — isolated Chromium (no setup required)**

Launches its own Chromium with a persistent profile at
`~/.voice-assistant/browser-profile/`. Cookies and logins persist between
calls. WhatsApp Web requires a one-time QR-code scan from your phone; after
that, `send_whatsapp_message` is fully automatic.

**Attached to your existing Chrome (recommended for WhatsApp)**

If you launch Chrome with `--remote-debugging-port=9222`, the assistant
detects this automatically and attaches to your running browser via the
Chrome DevTools Protocol (CDP). Your real tabs — including any already-open
`web.whatsapp.com` tab — are reused, so no QR-code scan is needed.

```bash
# Linux / macOS
google-chrome --remote-debugging-port=9222
# or for Chromium:
chromium --remote-debugging-port=9222
```

You can also set `VA_CHROME_CDP_PORT=<port>` to override the default 9222.

If Chrome is not reachable on the configured port, the assistant silently
falls back to its own isolated browser — no error, no configuration required.

## Conversation history

Every turn is appended to `~/.voice-assistant/history.jsonl`. The GUI shows
the last 50 exchanges on open. Run `voice-assistant --text` or `--gui` to
resume a prior session seamlessly.

## What this is not

- A product. There is no installer, auto-update, multi-user, or billing.
- Available on mobile or web — desktop only.

## License

MIT — see [LICENSE](LICENSE).
