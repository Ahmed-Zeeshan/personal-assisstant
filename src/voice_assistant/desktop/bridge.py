from __future__ import annotations
from collections.abc import Callable
from pathlib import Path
from typing import Any
import yaml
from voice_assistant.config import Config
from voice_assistant.setup_wizard import (
    DEFAULT_MODELS, WizardAnswers, render_config, render_env, PROVIDER_ENV_VAR,
)
from voice_assistant.desktop.events import EventBus


def _config_to_dict(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        raw = yaml.safe_load(path.read_text())
        cfg = Config.model_validate(raw)
    except Exception:
        return None
    return {
        "provider": cfg.brain.provider,
        "model":    cfg.brain.model,
        "hotkey":   cfg.audio.hotkey,
        "allowed_roots": [str(p) for p in cfg.safety.allowed_roots],
        "ollama_base_url": None,
    }


def _default_config_dict() -> dict[str, Any]:
    return {
        "provider": "anthropic",
        "model":    DEFAULT_MODELS["anthropic"],
        "hotkey":   "ctrl+shift+space",
        "allowed_roots": ["~"],
        "ollama_base_url": None,
    }


class Bridge:
    """JS-callable surface. All methods MUST be JSON-safe in/out."""

    def __init__(
        self,
        *,
        config_path: Path,
        env_path: Path,
        bus: EventBus,
        on_send_text: Callable[[str], None],
        on_listening_start: Callable[[], None],
        on_listening_stop: Callable[[], None],
    ) -> None:
        self._config_path = config_path
        self._env_path = env_path
        self._bus = bus
        self._on_send_text = on_send_text
        self._on_listening_start = on_listening_start
        self._on_listening_stop = on_listening_stop

    # ---- methods JS calls --------------------------------------------------
    def start_listening(self) -> None:
        self._on_listening_start()

    def stop_listening(self) -> None:
        self._on_listening_stop()

    def send_text(self, text: str) -> None:
        self._on_send_text(text)

    def get_config(self) -> dict[str, Any]:
        return _config_to_dict(self._config_path) or _default_config_dict()

    def save_config(self, cfg: dict[str, Any]) -> dict[str, Any]:
        try:
            provider = cfg["provider"]
            if provider not in PROVIDER_ENV_VAR:
                raise ValueError(f"unknown provider: {provider!r}")
            roots = [Path(p) for p in (cfg.get("allowed_roots") or ["~"])]
            answers = WizardAnswers(
                provider=provider,
                model=cfg["model"],
                hotkey=cfg["hotkey"],
                allowed_roots=roots,
                ollama_base_url=cfg.get("ollama_base_url"),
            )
            yaml_text = render_config(answers)
            Config.model_validate(yaml.safe_load(yaml_text))  # validation
        except Exception as exc:
            return {"ok": False, "errors": [str(exc)]}

        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._env_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(yaml_text)

        secret = cfg.get("_secret")
        if not secret and provider == "ollama":
            secret = cfg.get("ollama_base_url") or "http://localhost:11434"
        if secret:
            existing = self._env_path.read_text() if self._env_path.exists() else ""
            self._env_path.write_text(render_env(provider, secret, existing=existing))
            try:
                self._env_path.chmod(0o600)
            except OSError:
                pass

        # Emit fresh config event so the UI re-renders.
        self._bus.publish({"type": "config", "cfg": _config_to_dict(self._config_path) or _default_config_dict()})
        return {"ok": True}

    def quit(self) -> None:
        # Window close is handled in window.py; this is a hook for the JS quit shortcut.
        pass
