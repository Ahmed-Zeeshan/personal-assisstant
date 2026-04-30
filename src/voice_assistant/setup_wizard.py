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


import getpass

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
