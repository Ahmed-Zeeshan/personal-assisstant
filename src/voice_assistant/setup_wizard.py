from __future__ import annotations

import getpass
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

Provider = Literal["anthropic", "openai", "gemini", "ollama"]


@dataclass(frozen=True)
class WizardAnswers:
    provider: Provider
    model: str
    hotkey: str
    allowed_roots: list[Path]
    ollama_base_url: str | None  # only for provider == "ollama"
    user_name: str | None = None
    user_address_as: Literal["first_name", "full_name", "title", "none"] = "none"
    user_title: str | None = None
    voice: str = "piper:en_US-amy-medium"
    stt_language: str = "auto"
    avatar: str = "aria"
    respond_in: str = "auto"   # "auto" or ISO language code e.g. "ur", "hi"
    audio_trigger: str = "hotkey"
    wake_word: str = "hey_jarvis"
    wake_sensitivity: float = 0.5


def render_config(a: WizardAnswers) -> str:
    """Render answers to a complete config.yaml YAML string.

    The output must validate via voice_assistant.config.Config.
    """
    roots_block = "\n".join(f'    - "{p}"' for p in a.allowed_roots)
    base = (
        "brain:\n"
        f"  provider: {a.provider}\n"
        f"  model: {a.model}\n"
        "\n"
        "stt:\n"
        "  engine: faster-whisper\n"
        "  model: small\n"
        f"  language: {a.stt_language}\n"
        "\n"
        "tts:\n"
        "  engine: piper\n"
        f"  voice: {a.voice}\n"
        "\n"
        "audio:\n"
        f"  trigger: {a.audio_trigger}\n"
        f"  hotkey: {a.hotkey}\n"
        "  silence_seconds: 1.5\n"
        f"  wake_word: {a.wake_word}\n"
        f"  wake_sensitivity: {a.wake_sensitivity}\n"
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
        "\n"
        f"avatar: {a.avatar}\n"
    )
    user_block = ""
    has_user = a.user_name or a.user_address_as != "none" or a.respond_in != "auto"
    if has_user:
        d: dict[str, Any] = {"user": {"name": a.user_name, "address_as": a.user_address_as}}
        if a.user_title:
            d["user"]["title"] = a.user_title
        if a.respond_in != "auto":
            d["user"]["respond_in"] = a.respond_in
        user_block = "\n" + yaml.safe_dump(d, sort_keys=False, default_flow_style=False)
    return base + user_block


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


DEFAULT_MODELS: dict[Provider, str] = {
    "anthropic": "claude-haiku-4-5",     # was claude-sonnet-4-6 — haiku is ~3-4x faster
    "openai":    "gpt-5.4-mini",         # was gpt-5.5
    "gemini":    "gemini-3.1-flash",     # was gemini-3.1-pro
    "ollama":    "qwen3:14b",
}

# Curated lists of currently-supported models per provider, newest/best first.
# Deprecated models (gemini-1.5-*, gpt-3.5-*) are intentionally absent.
MODELS_BY_PROVIDER: dict[Provider, list[str]] = {
    "anthropic": [
        "claude-opus-4-7",        # most capable
        "claude-sonnet-4-6",      # balanced — default
        "claude-haiku-4-5",       # fastest / cheapest
    ],
    "openai": [
        "gpt-5.5",                # frontier (default)
        "gpt-5.4",                # standard
        "gpt-5.4-mini",           # fast, cheap
        "gpt-4o",                 # legacy production
    ],
    "gemini": [
        "gemini-3.1-pro",         # frontier (default)
        "gemini-3.1-flash",       # fast
        "gemini-2.5-flash",       # still supported
    ],
    "ollama": [
        "qwen3:14b",              # balanced default
        "llama3.3:70b",           # large general-purpose
        "qwen3.6:27b",            # coding-focused
        "qwen3-coder:30b",        # long-context coding
        "gemma3:4b",              # small / fast
    ],
}

_PROVIDER_LABELS: dict[Provider, str] = {
    "anthropic": "Anthropic Claude",
    "openai":    "OpenAI GPT",
    "gemini":    "Google Gemini",
    "ollama":    "Ollama (local)",
}

_PROVIDER_MENU: list[tuple[Provider, str]] = [
    ("anthropic", "Anthropic Claude    (recommended)"),
    ("openai",    "OpenAI GPT"),
    ("gemini",    "Google Gemini"),
    ("ollama",    "Ollama (local, no API key)"),
]

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


def _supports_color() -> bool:
    """Heuristic: enable ANSI colour iff stdout is a TTY and NO_COLOR is unset."""
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


class _C:
    """ANSI colour helpers that no-op on non-TTY stdout."""
    @staticmethod
    def _wrap(code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if _supports_color() else text

    @classmethod
    def bold(cls, t: str) -> str:    return cls._wrap("1", t)
    @classmethod
    def dim(cls, t: str) -> str:     return cls._wrap("2", t)
    @classmethod
    def violet(cls, t: str) -> str:  return cls._wrap("38;5;141", t)
    @classmethod
    def green(cls, t: str) -> str:   return cls._wrap("32", t)
    @classmethod
    def cyan(cls, t: str) -> str:    return cls._wrap("36", t)


def _print_welcome_banner() -> None:
    """Polished wizard intro: title, brief subtitle, and a hairline separator."""
    width = 56
    bar = "─" * width
    print()
    print(_C.violet("╭" + bar + "╮"))
    title = "voice-assistant — setup".center(width)
    sub   = "Pick an LLM, paste your key, you're done.".center(width)
    print(_C.violet("│") + _C.bold(title) + _C.violet("│"))
    print(_C.violet("│") + _C.dim(sub) + _C.violet("│"))
    print(_C.violet("╰" + bar + "╯"))
    print()


def _print_completion_banner(answers: WizardAnswers, config_path: Path, env_path: Path) -> None:
    """Polished post-wizard summary card with the configured choices and next steps."""
    width = 56
    bar = "─" * width

    def _row(label: str, value: str) -> str:
        # Pad to fit inside the box. Account for ANSI escape codes in length math.
        body = f"  {label}{value}"
        pad = max(0, width - len(body))
        return _C.violet("│") + _C.dim(f"  {label}") + value + " " * pad + _C.violet("│")

    provider_label = _PROVIDER_LABELS[answers.provider]
    secret_label = "API key" if answers.provider != "ollama" else "Base URL"

    print()
    print(_C.violet("╭" + bar + "╮"))
    # Centred title row (manual padding because of ANSI codes)
    raw_title = "✓ voice-assistant configured"
    pad = (width - len(raw_title)) // 2
    print(_C.violet("│") + " " * pad + _C.green("✓ ") + _C.bold("voice-assistant configured") + " " * (width - pad - len(raw_title)) + _C.violet("│"))
    print(_C.violet("│") + " " * width + _C.violet("│"))
    print(_row("Provider:  ", provider_label))
    print(_row("Model:     ", answers.model))
    print(_row("Hotkey:    ", answers.hotkey))
    print(_C.violet("│") + " " * width + _C.violet("│"))
    print(_row("Config:    ", str(config_path)))
    print(_row(f"{secret_label}:   ", str(env_path)))
    print(_C.violet("│") + " " * width + _C.violet("│"))
    next_hdr = "  What's next:"
    print(_C.violet("│") + _C.bold(next_hdr) + " " * (width - len(next_hdr)) + _C.violet("│"))
    bullets = [
        "    • Run:  voice-assistant",
        f"    • Press {answers.hotkey} to talk",
        "    • Switch provider:  voice-assistant --setup",
    ]
    for b in bullets:
        print(_C.violet("│") + b + " " * (width - len(b)) + _C.violet("│"))
    print(_C.violet("╰" + bar + "╯"))
    print()


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

    _print_welcome_banner()

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

        print("\n6) What should the assistant call you?")
        print("     [1] By my first name")
        print("     [2] By my full name")
        print("     [3] As 'Sir' / 'Ma'am' / a title")
        print("     [4] Don't address me by name")
        choice = input("   > ").strip() or "4"
        user_name: str | None = None
        user_address_as: Literal["first_name", "full_name", "title", "none"] = "none"
        user_title: str | None = None
        if choice in ("1", "2", "3"):
            user_name = _prompt_with_default("\n   Your name", "")
            if not user_name:
                user_address_as = "none"
            elif choice == "1":
                user_address_as = "first_name"
            elif choice == "2":
                user_address_as = "full_name"
            elif choice == "3":
                user_address_as = "title"
                user_title = _prompt_with_default("   Title", "Sir")
        voice = _prompt_with_default(
            "\n7) Voice (e.g. openai:nova for premium multilingual)", "piper:en_US-amy-medium"
        )
        stt_lang = _prompt_with_default(
            "\n8) Speech recognition language (auto, en, ur, hi, …)", "auto"
        )
    except (KeyboardInterrupt, EOFError):
        print("\nsetup cancelled, no files written")
        raise SystemExit(130) from None

    answers = WizardAnswers(
        provider=provider,
        model=model,
        hotkey=hotkey,
        allowed_roots=allowed_roots,
        ollama_base_url=secret if provider == "ollama" else None,
        user_name=user_name,
        user_address_as=user_address_as,
        user_title=user_title,
        voice=voice,
        stt_language=stt_lang,
        avatar="aria",
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

    _print_completion_banner(answers, config_path, env_path)
