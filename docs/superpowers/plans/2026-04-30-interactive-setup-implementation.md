# Interactive Setup Wizard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the wizard described in `docs/superpowers/specs/2026-04-30-interactive-setup-design.md` — a `voice-assistant --setup` command that interactively writes `config.yaml` and `.env`, plus install-script integration that runs the wizard automatically after `pip install`.

**Architecture:** New module `src/voice_assistant/setup_wizard.py` exposes `run_wizard()` (interactive) and `render_config()` (pure). `cli.py` gets a `--setup` flag. The two install scripts call `voice-assistant --setup --force` as their last step (skippable).

**Tech Stack:** Python 3.10+ · pydantic (already a dep) · PyYAML (already a dep) · `getpass` stdlib · `python-dotenv` (already a dep) · pytest with `monkeypatch`.

---

## File Structure

**Created:**
- `src/voice_assistant/setup_wizard.py` — wizard module
- `tests/test_setup_wizard.py` — unit tests

**Modified:**
- `src/voice_assistant/cli.py` — add `--setup` and `--force` flags
- `scripts/install.sh` — call wizard at end (gated)
- `scripts/install.ps1` — same on Windows
- `website/src/data/site.ts` — install-flow copy update
- `config.yaml.example` — log file path corrected to user-home location

---

## Task 1: Pure rendering function + dataclass

**Files:**
- Create: `src/voice_assistant/setup_wizard.py`
- Create: `tests/test_setup_wizard.py`

- [ ] **Step 1: Write failing test for `render_config`**

```python
# tests/test_setup_wizard.py
from pathlib import Path
import yaml
from voice_assistant.setup_wizard import WizardAnswers, render_config
from voice_assistant.config import Config


def _answers(**overrides):
    base = dict(
        provider="anthropic",
        model="claude-sonnet-4-6",
        hotkey="ctrl+shift+space",
        allowed_roots=[Path("~")],
        ollama_base_url=None,
    )
    base.update(overrides)
    return WizardAnswers(**base)


def test_render_config_for_anthropic_is_valid_config():
    yaml_text = render_config(_answers())
    parsed = yaml.safe_load(yaml_text)
    cfg = Config.model_validate(parsed)
    assert cfg.brain.provider == "anthropic"
    assert cfg.brain.model == "claude-sonnet-4-6"
    assert cfg.audio.hotkey == "ctrl+shift+space"
    assert str(cfg.logging.file).endswith("voice-assistant.log")


def test_render_config_for_each_provider_validates():
    for provider, model in [
        ("anthropic", "claude-sonnet-4-6"),
        ("openai", "gpt-4o"),
        ("gemini", "gemini-1.5-pro"),
        ("ollama", "llama3.1:8b"),
    ]:
        yaml_text = render_config(_answers(provider=provider, model=model))
        cfg = Config.model_validate(yaml.safe_load(yaml_text))
        assert cfg.brain.provider == provider
        assert cfg.brain.model == model
```

- [ ] **Step 2: Run the failing test**

```bash
pytest tests/test_setup_wizard.py -v
```

Expected: ImportError for `voice_assistant.setup_wizard`.

- [ ] **Step 3: Implement `WizardAnswers` and `render_config`**

```python
# src/voice_assistant/setup_wizard.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


Provider = Literal["anthropic", "openai", "gemini", "ollama"]


@dataclass(frozen=True)
class WizardAnswers:
    provider: Provider
    model: str
    hotkey: str
    allowed_roots: list[Path]
    ollama_base_url: str | None  # only for provider == "ollama"


def render_config(a: WizardAnswers) -> str:
    """Render answers to a complete config.yaml YAML string.

    The output must validate via voice_assistant.config.Config.
    """
    roots_block = "\n".join(f'    - "{p}"' for p in a.allowed_roots)
    return (
        "brain:\n"
        f"  provider: {a.provider}\n"
        f"  model: {a.model}\n"
        "\n"
        "stt:\n"
        "  engine: faster-whisper\n"
        "  model: small\n"
        "  language: en\n"
        "\n"
        "tts:\n"
        "  engine: piper\n"
        "  voice: en_US-amy-medium\n"
        "\n"
        "audio:\n"
        "  trigger: hotkey\n"
        f"  hotkey: {a.hotkey}\n"
        "  silence_seconds: 1.5\n"
        "\n"
        "safety:\n"
        "  allowed_roots:\n"
        f"{roots_block}\n"
        "  destructive_requires_confirmation: true\n"
        "  delete_rate_per_minute: 5\n"
        "\n"
        "gmail:\n"
        "  credentials_file: ~/.voice-assistant/gmail-creds.json\n"
        "\n"
        "logging:\n"
        "  level: INFO\n"
        "  file: ~/.voice-assistant/voice-assistant.log\n"
    )
```

- [ ] **Step 4: Tests pass**

```bash
pytest tests/test_setup_wizard.py -v
```

Expected: 2/2 pass.

- [ ] **Step 5: Commit**

```bash
git add src/voice_assistant/setup_wizard.py tests/test_setup_wizard.py
git commit -m "feat(setup): WizardAnswers + render_config (pure)"
```

---

## Task 2: `.env` rendering with stale-key removal

**Files:**
- Modify: `src/voice_assistant/setup_wizard.py`
- Modify: `tests/test_setup_wizard.py`

- [ ] **Step 1: Add failing test**

```python
# Append to tests/test_setup_wizard.py
from voice_assistant.setup_wizard import (
    PROVIDER_ENV_VAR,
    render_env,
)


def test_render_env_for_each_provider_writes_correct_key():
    for provider, expected_var in PROVIDER_ENV_VAR.items():
        env = render_env(provider, "secret-value", existing="")
        assert f"{expected_var}=secret-value" in env


def test_render_env_strips_other_provider_keys():
    existing = (
        "ANTHROPIC_API_KEY=old-anthropic-key\n"
        "OPENAI_API_KEY=old-openai-key\n"
        "FOO=bar\n"
    )
    env = render_env("gemini", "new-gemini-key", existing=existing)
    assert "ANTHROPIC_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "GEMINI_API_KEY=new-gemini-key" in env
    assert "FOO=bar" in env  # unrelated keys preserved


def test_render_env_for_ollama_writes_base_url():
    env = render_env("ollama", "http://localhost:11434", existing="")
    assert "OLLAMA_BASE_URL=http://localhost:11434" in env
    assert "ANTHROPIC_API_KEY" not in env
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_setup_wizard.py -v
```

Expected: 3 failures with "cannot import PROVIDER_ENV_VAR / render_env".

- [ ] **Step 3: Implement `PROVIDER_ENV_VAR` and `render_env`**

Append to `src/voice_assistant/setup_wizard.py`:

```python
PROVIDER_ENV_VAR: dict[Provider, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai":    "OPENAI_API_KEY",
    "gemini":    "GEMINI_API_KEY",
    "ollama":    "OLLAMA_BASE_URL",
}

_MANAGED_VARS: frozenset[str] = frozenset(PROVIDER_ENV_VAR.values())


def render_env(provider: Provider, value: str, *, existing: str) -> str:
    """Return new .env contents.

    Replaces any managed variable (one of `_MANAGED_VARS`) with the new
    `provider`-specific key. Preserves unrelated lines verbatim.
    """
    keep: list[str] = []
    for line in existing.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            keep.append(line)
            continue
        head, _, _ = stripped.partition("=")
        if head in _MANAGED_VARS:
            continue  # drop stale managed key
        keep.append(line)

    new_var = PROVIDER_ENV_VAR[provider]
    keep.append(f"{new_var}={value}")
    # Always end with a newline.
    return "\n".join(keep) + "\n"
```

- [ ] **Step 4: Tests pass**

```bash
pytest tests/test_setup_wizard.py -v
```

Expected: 5/5 pass.

- [ ] **Step 5: Commit**

```bash
git add src/voice_assistant/setup_wizard.py tests/test_setup_wizard.py
git commit -m "feat(setup): render_env with stale-key removal"
```

---

## Task 3: `run_wizard` interactive prompts

**Files:**
- Modify: `src/voice_assistant/setup_wizard.py`
- Modify: `tests/test_setup_wizard.py`

- [ ] **Step 1: Add failing tests for `run_wizard`**

```python
# Append to tests/test_setup_wizard.py
import os
import sys
import pytest
from voice_assistant.setup_wizard import run_wizard


def _patch_io(monkeypatch, inputs: list[str], passwords: list[str]):
    input_iter = iter(inputs)
    pw_iter = iter(passwords)
    monkeypatch.setattr("builtins.input", lambda *_: next(input_iter))
    monkeypatch.setattr("getpass.getpass", lambda *_: next(pw_iter))


def test_wizard_writes_anthropic_config_and_env(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    _patch_io(monkeypatch, inputs=["1", "", "", ""], passwords=["sk-ant-test"])
    run_wizard(config_path=config_path, env_path=env_path)

    assert config_path.exists()
    assert env_path.exists()
    assert "ANTHROPIC_API_KEY=sk-ant-test" in env_path.read_text()
    assert "provider: anthropic" in config_path.read_text()


def test_wizard_writes_ollama_with_base_url_and_no_key(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    _patch_io(monkeypatch, inputs=["4", "", "", "", ""], passwords=[])
    run_wizard(config_path=config_path, env_path=env_path)

    assert "OLLAMA_BASE_URL=http://localhost:11434" in env_path.read_text()
    assert "provider: ollama" in config_path.read_text()


def test_wizard_aborts_on_existing_config_when_user_declines(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    config_path.write_text("# existing\n")
    _patch_io(monkeypatch, inputs=["n"], passwords=[])
    run_wizard(config_path=config_path, env_path=env_path)

    assert config_path.read_text() == "# existing\n"
    assert not env_path.exists()


def test_wizard_force_overwrites_existing(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    config_path.write_text("# existing\n")
    _patch_io(monkeypatch, inputs=["1", "", "", ""], passwords=["sk-ant-test"])
    run_wizard(config_path=config_path, env_path=env_path, force=True)

    assert "provider: anthropic" in config_path.read_text()


def test_wizard_writes_env_with_mode_0600(tmp_path, monkeypatch):
    if sys.platform == "win32":
        pytest.skip("file modes are POSIX-only")
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    _patch_io(monkeypatch, inputs=["1", "", "", ""], passwords=["sk-ant-test"])
    run_wizard(config_path=config_path, env_path=env_path)

    mode = oct(env_path.stat().st_mode & 0o777)
    assert mode == "0o600"
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_setup_wizard.py -v
```

Expected: 5 new failures (existing 5 still pass).

- [ ] **Step 3: Implement `run_wizard`**

Append to `src/voice_assistant/setup_wizard.py`:

```python
import getpass
from pathlib import Path

DEFAULT_MODELS: dict[Provider, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai":    "gpt-4o",
    "gemini":    "gemini-1.5-pro",
    "ollama":    "llama3.1:8b",
}

_PROVIDER_MENU: list[tuple[Provider, str]] = [
    ("anthropic", "Anthropic Claude    (recommended)"),
    ("openai",    "OpenAI GPT"),
    ("gemini",    "Google Gemini"),
    ("ollama",    "Ollama (local, no API key)"),
]

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


def _prompt_provider() -> Provider:
    print("1) Pick your LLM provider:")
    for i, (_, label) in enumerate(_PROVIDER_MENU, 1):
        print(f"     [{i}] {label}")
    for _ in range(3):
        choice = input("   > ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(_PROVIDER_MENU):
            return _PROVIDER_MENU[int(choice) - 1][0]
        for p, _ in _PROVIDER_MENU:
            if choice.lower() == p:
                return p
        print(f"   pick 1-{len(_PROVIDER_MENU)} or a name")
    raise SystemExit("setup cancelled — too many invalid inputs")


def _prompt_with_default(label: str, default: str) -> str:
    answer = input(f"{label} [{default}]: ").strip()
    return answer or default


def _prompt_secret(label: str) -> str:
    for _ in range(3):
        value = getpass.getpass(f"{label}: ").strip()
        if value:
            return value
        print("(empty input not accepted)")
    raise SystemExit("setup cancelled — too many invalid inputs")


def _prompt_overwrite(path: Path) -> bool:
    answer = input(f"{path} exists. Overwrite? [y/N] ").strip().lower()
    return answer == "y"


def run_wizard(
    *,
    config_path: Path,
    env_path: Path,
    force: bool = False,
) -> None:
    """Interactive wizard. Writes config_path and env_path on success."""
    if config_path.exists() and not force:
        if not _prompt_overwrite(config_path):
            print("setup skipped, existing config kept")
            return

    print("Voice-assistant setup")
    print("─────────────────────")

    try:
        provider = _prompt_provider()
        model = _prompt_with_default("\n2) Model name", DEFAULT_MODELS[provider])

        if provider == "ollama":
            secret = _prompt_with_default(
                "\n3) Ollama base URL", DEFAULT_OLLAMA_BASE_URL
            )
        else:
            secret = _prompt_secret(
                f"\n3) {provider.capitalize()} API key (hidden, paste & enter)"
            )

        hotkey = _prompt_with_default(
            "\n4) Hotkey to start listening", "ctrl+shift+space"
        )
        roots_raw = _prompt_with_default(
            "\n5) Folders the assistant may touch (comma-separated)", "~"
        )
        allowed_roots = [Path(p.strip()) for p in roots_raw.split(",") if p.strip()]
    except (KeyboardInterrupt, EOFError):
        print("\nsetup cancelled, no files written")
        raise SystemExit(130)

    answers = WizardAnswers(
        provider=provider,
        model=model,
        hotkey=hotkey,
        allowed_roots=allowed_roots,
        ollama_base_url=secret if provider == "ollama" else None,
    )

    config_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.parent.mkdir(parents=True, exist_ok=True)

    existing_env = env_path.read_text() if env_path.exists() else ""
    config_path.write_text(render_config(answers))
    env_path.write_text(render_env(provider, secret, existing=existing_env))
    try:
        env_path.chmod(0o600)
    except OSError:
        pass  # Windows / non-POSIX

    print(f"\n✓ wrote {config_path}")
    print(f"✓ wrote {env_path} (mode 0600)")
    print("\nRun:  voice-assistant")
```

- [ ] **Step 4: Tests pass**

```bash
pytest tests/test_setup_wizard.py -v
```

Expected: 10/10 pass.

- [ ] **Step 5: Commit**

```bash
git add src/voice_assistant/setup_wizard.py tests/test_setup_wizard.py
git commit -m "feat(setup): run_wizard interactive prompts"
```

---

## Task 4: Wire `--setup` into `cli.py`

**Files:**
- Modify: `src/voice_assistant/cli.py`
- Modify: `tests/test_setup_wizard.py`

- [ ] **Step 1: Add a CLI test**

```python
# Append to tests/test_setup_wizard.py
import subprocess


def test_cli_setup_flag_runs_wizard(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    inputs = iter(["1", "", "", ""])
    passwords = iter(["sk-ant-test"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda *_: next(passwords))
    monkeypatch.setattr(
        "voice_assistant.setup_wizard.run_wizard",
        lambda **kw: run_wizard(config_path=config_path, env_path=env_path, force=True),
    )
    monkeypatch.setattr("sys.argv", ["voice-assistant", "--setup", "--force"])

    from voice_assistant.cli import main
    main()

    assert config_path.exists()
    assert env_path.exists()
```

(Note: this test uses a monkeypatch of `run_wizard` to control where files land — the goal is verifying `cli.main()` dispatches to the wizard when `--setup` is passed.)

- [ ] **Step 2: Run failing test**

```bash
pytest tests/test_setup_wizard.py::test_cli_setup_flag_runs_wizard -v
```

Expected: failure ("unrecognized argument: --setup").

- [ ] **Step 3: Modify `cli.py`**

In `src/voice_assistant/cli.py`, replace the existing `argparse` block with:

```python
def main() -> None:
    parser = argparse.ArgumentParser(prog="voice-assistant")
    parser.add_argument(
        "--config", type=Path, default=Path("config.yaml"),
        help="Path to config file (default: ./config.yaml)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--text", action="store_true",
        help="Text mode: read prompts from stdin, no audio.",
    )
    mode.add_argument(
        "--setup", action="store_true",
        help="Run interactive setup wizard (writes config.yaml and .env).",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="With --setup: overwrite an existing config without prompting.",
    )
    args = parser.parse_args()

    if args.setup:
        from pathlib import Path as _P
        from voice_assistant.setup_wizard import run_wizard
        home = _P.home() / ".voice-assistant"
        run_wizard(
            config_path=home / "config.yaml",
            env_path=home / ".env",
            force=args.force,
        )
        return

    load_dotenv()
    cfg = load_config(args.config)
    # ... rest of main() unchanged
```

(Preserve every other line of `cli.py`. The change is: the `argparse` block adds a mutually-exclusive group around `--text`/`--setup`, adds `--force`, and the new `if args.setup:` early-return block.)

- [ ] **Step 4: Test passes**

```bash
pytest tests/test_setup_wizard.py -v
```

Expected: 11/11 pass.

- [ ] **Step 5: Commit**

```bash
git add src/voice_assistant/cli.py tests/test_setup_wizard.py
git commit -m "feat(cli): --setup flag dispatches to wizard"
```

---

## Task 5: Install-script integration

**Files:**
- Modify: `scripts/install.sh`
- Modify: `scripts/install.ps1`

- [ ] **Step 1: Edit `scripts/install.sh`**

Two edits.

**Edit A** — replace the existing config-seeding block (lines starting with `if [ ! -f "$CONFIG_DIR/config.yaml" ]`) with a wizard call. Find this block:

```bash
if [ ! -f "$CONFIG_DIR/config.yaml" ] && [ -f "$VA_HOME/.venv/share/voice-assistant/config.yaml.example" ]; then
  cp "$VA_HOME/.venv/share/voice-assistant/config.yaml.example" "$CONFIG_DIR/config.yaml"
  say "seeded $CONFIG_DIR/config.yaml from example"
fi

say "done. Set your API key in $CONFIG_DIR/.env, then run: voice-assistant"
```

Replace it with:

```bash
if [ "${SKIP_SETUP:-}" != "1" ]; then
  say "running setup wizard"
  if ! "$VA_HOME/.venv/bin/voice-assistant" --setup --force; then
    warn "setup wizard exited non-zero; re-run later with: voice-assistant --setup"
  fi
else
  say "skipping setup wizard (SKIP_SETUP=1)"
fi

say "done. Run: voice-assistant"
```

**Edit B** — accept `--no-setup` from the user. After the existing `[ "${1:-}" = "--uninstall" ] && uninstall` line, add:

```bash
if [ "${1:-}" = "--no-setup" ]; then
  export SKIP_SETUP=1
  shift
fi
```

- [ ] **Step 2: Edit `scripts/install.ps1`**

Find this block near the end:

```powershell
Say "done. Set your API key in $ConfigDir\.env, then run: voice-assistant"
```

Replace with:

```powershell
if ($env:SKIP_SETUP -ne '1' -and -not $NoSetup) {
  Say "running setup wizard"
  & $exe --setup --force
  if ($LASTEXITCODE -ne 0) {
    Warn "setup wizard exited non-zero; re-run later with: voice-assistant --setup"
  }
}

Say "done. Run: voice-assistant"
```

Add a `$NoSetup` parameter at the top of the script (just below the existing variable declarations):

```powershell
param([switch]$NoSetup)
```

(`param(...)` must be the very first non-comment statement in a `.ps1` file. Move the `$ErrorActionPreference = 'Stop'` line to come AFTER `param(...)`.)

- [ ] **Step 3: Verify shellcheck (if available)**

```bash
shellcheck scripts/install.sh || echo "shellcheck not installed, skipping"
```

If shellcheck reports anything new in the edited block, fix it.

- [ ] **Step 4: Run an end-to-end smoke test of the wizard alone**

```bash
cd /home/zeeshan-ahmed/voice-assistant
TMPDIR=$(mktemp -d)
printf "1\n\n\nctrl+f1\n~\n" | \
  python -m voice_assistant --setup --force \
  2>&1 || true  # password input requires actual stdin
```

Don't expect this to succeed end-to-end (getpass needs a real TTY); verify only that `--setup` is recognised and the wizard starts.

A more reliable smoke test:
```bash
pytest tests/test_setup_wizard.py -v
```

All 11 tests should still pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/install.sh scripts/install.ps1
git commit -m "feat(install): run setup wizard at end of install (skippable)"
```

---

## Task 6: Website install copy + final polish

**Files:**
- Modify: `website/src/data/site.ts`
- Modify: `config.yaml.example` (optional log-path correction)

- [ ] **Step 1: Update install notes in `website/src/data/site.ts`**

In each of the three `install.*.note` strings, change:

```
note: 'Default hotkey: ctrl+shift+space.'
```

to:

```
note: 'The installer asks for your LLM provider and API key. Default hotkey: ctrl+shift+space.'
```

(Apply to all three OS entries: macos, linux, windows.)

- [ ] **Step 2: Verify website still builds and Lighthouse passes**

```bash
cd website && npm run build && npm run check
```

Expected: build succeeds, all four Lighthouse thresholds still pass.

- [ ] **Step 3: Verify the config example matches the wizard's output**

Look at `config.yaml.example`. The wizard's `render_config` writes `logging.file: ~/.voice-assistant/voice-assistant.log` while the current example has `logging.file: logs/voice-assistant.log`. Keep both files internally consistent: this is intentional — the example is for development from the source tree, the wizard's output is for installed users. No change needed unless future readers find it confusing. **Skip this step** unless someone has flagged it.

- [ ] **Step 4: Commit**

```bash
git add website/src/data/site.ts
git commit -m "docs(website): mention setup wizard in install copy"
```

---

## Task 7: End-to-end verification + push

**Files:** none (verification only)

- [ ] **Step 1: Full test run**

```bash
cd /home/zeeshan-ahmed/voice-assistant
pytest -q
```

Expected: all tests pass (existing 93 + the new 11 = 104 passing).

- [ ] **Step 2: Run the wizard against a tmp directory by hand**

```bash
TMPDIR=$(mktemp -d)
cd /home/zeeshan-ahmed/voice-assistant
python -c "
from pathlib import Path
from voice_assistant.setup_wizard import run_wizard
run_wizard(
    config_path=Path('$TMPDIR/config.yaml'),
    env_path=Path('$TMPDIR/.env'),
    force=True,
)
"
# Walk through the prompts manually.
cat $TMPDIR/config.yaml
cat $TMPDIR/.env
ls -la $TMPDIR/.env  # confirm 0600
```

If anything looks wrong, fix it before continuing.

- [ ] **Step 3: Push**

```bash
git push origin main
```

- [ ] **Step 4: Done.**

The next user to `curl | bash` will get the wizard.

---

## Done criteria

- `pytest -q` passes (~104 tests).
- `voice-assistant --setup` runs the wizard from a fresh terminal.
- `voice-assistant --setup --force` skips the overwrite prompt.
- `voice-assistant --setup` and `voice-assistant --text` are mutually exclusive (argparse rejects passing both).
- `scripts/install.sh` and `scripts/install.ps1` call the wizard at the end and accept `--no-setup` / `-NoSetup` to skip it.
- `~/.voice-assistant/.env` is mode `0600` after wizard completion.
- The website's install notes reference the wizard.
- All commits pushed to `origin/main`.
