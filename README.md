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

The test suite is 93 tests covering safety, tools, brain wiring, orchestrator,
config, logging, audio capture, STT, TTS, and Gmail (mocked). Audio I/O and
hotkey listening are not unit-tested — those require real hardware.

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

## What this is not

- A product. There is no installer, auto-update, multi-user, or billing.
- Available on mobile or web — desktop only.
- Able to message via WhatsApp. WhatsApp has no safe API for personal numbers.

## License

Private. Not for redistribution.
