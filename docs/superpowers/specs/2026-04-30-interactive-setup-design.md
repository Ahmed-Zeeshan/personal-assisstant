# Interactive setup wizard — design

**Date:** 2026-04-30
**Status:** Approved
**Scope:** Replace the manual "edit `config.yaml` then edit `.env`" install dance with an interactive wizard, available both from the install scripts (runs once on install) and as a `voice-assistant --setup` reconfigure command.

## Goal

A new user runs the install one-liner and is asked, in plain English, which LLM provider they want and for their API key. The wizard writes a complete, validated `config.yaml` and a `0600`-mode `.env`. Switching providers later is one command — `voice-assistant --setup` — instead of editing two files. No silent defaults that produce a non-working install.

## Non-goals

- API-key validation via network calls (no surprise charges, no captive-portal failures).
- Account creation flows or OAuth for LLM providers.
- A graphical UI — terminal prompts only.
- A configuration management framework (no profiles, no environments, no `voice-assistant config get/set` API). One config, one `.env`, that's it.
- Migrating the website's "Install" tab away from the existing `curl | bash` pattern. The wizard simply runs after `pip install` finishes.

## High-level decisions

| Decision | Choice | Why |
|---|---|---|
| Where the wizard lives | New module `src/voice_assistant/setup_wizard.py`, exposed via `voice-assistant --setup` | Same codebase, same dependencies, same tests; reusable for reconfigure. |
| When it runs on install | Last step of `install.sh` / `install.ps1`, after `pip install` succeeds | Single end-to-end ramp from `curl` to working binary. |
| CI escape hatch | `install.sh --no-setup` and `install.ps1 -NoSetup` | Containerised installs and CI shouldn't block on stdin. |
| API-key validation | Shape only (non-empty, no whitespace, prefix sniff per provider) | Network validation is fragile and slow. Shape-fail is fast. |
| Existing-config behaviour | If `~/.voice-assistant/config.yaml` exists, prompt before overwriting | Don't clobber a tweaked config. |
| Config-file format | Keep YAML; write fresh on each setup run (no comment-preserving round-trip) | Comment preservation is a YAML library wart we don't need. |
| API-key storage | `~/.voice-assistant/.env`, mode `0600` | Same pattern as the existing OAuth token. Loaded by `python-dotenv` (already a dep). |
| Hidden input for keys | `getpass.getpass()` (stdlib) | API keys never echo to the terminal. |
| Providers covered | `anthropic`, `openai`, `gemini`, `ollama` | Matches the existing `BrainConfig.provider` Literal. |

## Architecture

### Module layout

```
src/voice_assistant/
├── setup_wizard.py            # NEW — pure-Python interactive prompts + file writes
├── cli.py                     # MODIFIED — add `--setup` flag
└── config.py                  # UNTOUCHED — existing pydantic models stay authoritative

tests/
├── test_setup_wizard.py       # NEW — input/output golden tests using monkeypatched stdin

scripts/
├── install.sh                 # MODIFIED — call `voice-assistant --setup` at the end (skippable via --no-setup)
└── install.ps1                # MODIFIED — same on Windows (-NoSetup)
```

The wizard module exports two functions:

```python
def run_wizard(
    config_path: Path = Path.home() / ".voice-assistant" / "config.yaml",
    env_path:   Path = Path.home() / ".voice-assistant" / ".env",
    *, force: bool = False,
) -> None:
    """Interactive prompts → validated config + .env on disk."""

def render_config(answers: WizardAnswers) -> str:
    """Pure function: WizardAnswers → YAML string. Used by the wizard and tested directly."""
```

`WizardAnswers` is a frozen dataclass with one field per question. This separation lets the tests cover the rendering without touching stdin.

### Data flow

```
$ voice-assistant --setup
       │
       ▼
cli.main() sees --setup
       │
       ▼
setup_wizard.run_wizard()
       │
       ├── if config_path exists and not --force: prompt overwrite ──► abort if no
       │
       ├── prompt: provider          (anthropic | openai | gemini | ollama)
       ├── prompt: model             (default per provider, override allowed)
       ├── prompt: API key           (hidden; skipped for ollama)
       ├── prompt: ollama base URL   (only if provider == ollama)
       ├── prompt: hotkey            (default ctrl+shift+space)
       ├── prompt: allowed_roots     (default ~)
       │
       ├── render_config(answers)    → YAML string
       │
       ├── write config_path         (mode 0644)
       ├── write env_path            (mode 0600, only the relevant key)
       │
       └── print summary + next step
```

### CLI surface

`cli.py` gains one new argument:

```python
parser.add_argument(
    "--setup", action="store_true",
    help="Run interactive setup wizard (writes config.yaml and .env).",
)
parser.add_argument(
    "--force", action="store_true",
    help="With --setup: overwrite an existing config without prompting.",
)
```

`--setup` is mutually exclusive with `--text` (argparse handles this with `add_mutually_exclusive_group`). When `--setup` is specified, the wizard runs and the process exits before any orchestrator setup.

### Install-script integration

`install.sh` adds a final block:

```bash
if [ "${SKIP_SETUP:-}" != "1" ]; then
  say "running setup wizard"
  "$VA_HOME/.venv/bin/voice-assistant" --setup --force || warn "setup wizard exited non-zero; you can re-run with: voice-assistant --setup"
fi
```

The `--no-setup` flag and `SKIP_SETUP=1` env var both skip this block. The `--force` flag here is appropriate because we just installed the package — there is no existing config to protect.

`install.ps1` mirrors this with `-NoSetup` and `$env:SKIP_SETUP`.

## Wizard prompts (verbatim)

The wizard uses plain `input()` for visible answers and `getpass.getpass()` for keys. Defaults appear in brackets. Empty input takes the default.

```
Voice-assistant setup
─────────────────────
1) Pick your LLM provider:
     [1] Anthropic Claude    (recommended)
     [2] OpenAI GPT
     [3] Google Gemini
     [4] Ollama (local, no API key)
   > 1

2) Model name [claude-sonnet-4-6]: ↵

3) Anthropic API key (hidden, paste & enter):
   > ········

4) Hotkey to start listening [ctrl+shift+space]: ↵

5) Folders the assistant may touch (comma-separated) [~]: ↵

✓ wrote /home/you/.voice-assistant/config.yaml
✓ wrote /home/you/.voice-assistant/.env (mode 0600)

Run:  voice-assistant
```

For ollama, prompt 3 is skipped and replaced by:

```
3a) Ollama base URL [http://localhost:11434]: ↵
```

The `OLLAMA_BASE_URL` env var (rather than an API key) is what `litellm` consumes. It goes in `.env`.

## Default models per provider

| Provider | Default model | Env var | Key shape sniff |
|---|---|---|---|
| anthropic | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` | starts with `sk-ant-` |
| openai | `gpt-4o` | `OPENAI_API_KEY` | starts with `sk-` |
| gemini | `gemini-1.5-pro` | `GEMINI_API_KEY` | non-empty, no whitespace |
| ollama | `llama3.1:8b` | `OLLAMA_BASE_URL` | URL parse with `urllib` |

If the key shape doesn't match, the wizard re-prompts with `That doesn't look like a {provider} API key. Try again?` and a `(continue anyway)` option after two failed tries — we can't be 100% certain of every key format and shouldn't be prescriptive.

## File outputs

### `~/.voice-assistant/config.yaml` (mode 0644)

Rendered fresh each setup. Sample for Anthropic:

```yaml
brain:
  provider: anthropic
  model: claude-sonnet-4-6

stt:
  engine: faster-whisper
  model: small
  language: en

tts:
  engine: piper
  voice: en_US-amy-medium

audio:
  trigger: hotkey
  hotkey: ctrl+shift+space
  silence_seconds: 1.5

safety:
  allowed_roots:
    - "~"
  destructive_requires_confirmation: true
  delete_rate_per_minute: 5

gmail:
  credentials_file: ~/.voice-assistant/gmail-creds.json

logging:
  level: INFO
  file: ~/.voice-assistant/voice-assistant.log
```

Note: `logging.file` defaults to `~/.voice-assistant/voice-assistant.log` rather than the example's `logs/voice-assistant.log` because the wizard writes a config that runs from `$HOME`, not from the source tree.

### `~/.voice-assistant/.env` (mode 0600)

Contains exactly one secret line per setup:

```
ANTHROPIC_API_KEY=sk-ant-***
```

If the file already exists with other keys, the wizard *adds* the new key for the chosen provider and *removes* keys for previously-selected providers (so re-running with a different provider doesn't leave stale keys behind). The file is rewritten via a deterministic `dict→lines` render.

## Error handling

| Failure | Behaviour |
|---|---|
| User Ctrl-C during wizard | Print `setup cancelled, no files written`, exit 130. |
| Existing config + user declines overwrite | Exit 0 with message `setup skipped, existing config kept`. |
| Cannot create `~/.voice-assistant/` | Print error, suggest `mkdir`, exit 1. |
| Cannot write `.env` (permission) | Print error, exit 1. The config file is not written either (atomic — both or neither). |
| Pydantic validation fails on the rendered config | Print the validation error, exit 1. The wizard's defaults must always validate; a failure here is a bug. |
| Empty input where no default exists | Re-prompt. |
| Three failed re-prompts on the same field | Print `setup cancelled — too many invalid inputs`, exit 1. |

## Testing

Tests in `tests/test_setup_wizard.py`:

- **Pure rendering** — `render_config(WizardAnswers(provider="anthropic", model="x", ...))` produces the expected YAML; load_config can parse the output.
- **Each provider path** — wizard writes the right `.env` key (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `OLLAMA_BASE_URL`).
- **Existing config + decline** — wizard exits 0, files unchanged.
- **Existing config + accept** — wizard overwrites both files.
- **Existing `.env` with stale keys** — old keys are removed, new key is the only one.
- **Stale-key removal preserves unrelated env vars** — `FOO=bar` stays.
- **File modes** — `config.yaml` is `0644`, `.env` is `0600`.
- **Key shape sniff** — pasting `wrong-format` for anthropic re-prompts; `sk-ant-abc` accepts.
- **Ctrl-C / EOF** — wizard handles `KeyboardInterrupt` and `EOFError` gracefully.
- **`--force`** — skips overwrite prompt.

Stdin is fed via `monkeypatch.setattr("builtins.input", iter([...]).__next__)` and `monkeypatch.setattr("getpass.getpass", iter([...]).__next__)`. No subprocess spawning, no slow tests.

The existing `test_filesystem_tools.py`, `test_brain.py`, etc. are not touched.

## Website updates

`website/src/data/site.ts` install copy changes from:

> Then run `voice-assistant`. Default hotkey: ctrl+shift+space.

to:

> The installer asks for your LLM provider and API key, then you're done. Default hotkey: ctrl+shift+space.

The Hero subhead and Features text don't need to change.

## Open questions / deferred decisions

- **Re-running the wizard from inside the running assistant** — `voice-assistant --setup` from a fresh terminal is enough. No "live reconfigure" command.
- **Multiple profiles** — out of scope; single config, single `.env`.
- **GUI variant** — out of scope; terminal only.
