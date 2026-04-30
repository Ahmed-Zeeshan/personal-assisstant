from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from voice_assistant.config import Config
from voice_assistant.desktop.events import EventBus
from voice_assistant.setup_wizard import (
    DEFAULT_MODELS,
    MODELS_BY_PROVIDER,
    PROVIDER_ENV_VAR,
    WizardAnswers,
    render_config,
    render_env,
)

if TYPE_CHECKING:
    from voice_assistant.history import History

log = logging.getLogger(__name__)


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
        "user_name":       cfg.user.name,
        "user_address_as": cfg.user.address_as,
        "user_title":      cfg.user.title,
    }


def _default_config_dict() -> dict[str, Any]:
    return {
        "provider": "anthropic",
        "model":    DEFAULT_MODELS["anthropic"],
        "hotkey":   "ctrl+shift+space",
        "allowed_roots": ["~"],
        "ollama_base_url": None,
        "user_name":       None,
        "user_address_as": "none",
        "user_title":      None,
    }


def _has_secret_for(provider: str, env_path: Path) -> bool:
    """Return True iff env_path contains a non-empty value for the provider's key."""
    if provider not in PROVIDER_ENV_VAR or not env_path.exists():
        return False
    var = PROVIDER_ENV_VAR[provider]
    prefix = f"{var}="
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith(prefix) and len(line) > len(prefix):
            return True
    return False


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
        on_config_reload: Callable[[], None] | None = None,
        history: History | None = None,
    ) -> None:
        self._config_path = config_path
        self._env_path = env_path
        self._bus = bus
        self._on_send_text = on_send_text
        self._on_listening_start = on_listening_start
        self._on_listening_stop = on_listening_stop
        self._on_config_reload = on_config_reload
        self._history = history

    # ---- methods JS calls --------------------------------------------------
    def start_listening(self) -> None:
        self._on_listening_start()

    def stop_listening(self) -> None:
        self._on_listening_stop()

    def send_text(self, text: str) -> None:
        self._on_send_text(text)

    def get_config(self) -> dict[str, Any]:
        cfg = _config_to_dict(self._config_path) or _default_config_dict()
        cfg["has_secret"] = _has_secret_for(cfg["provider"], self._env_path)
        cfg["available_models"] = {p: list(m) for p, m in MODELS_BY_PROVIDER.items()}
        return cfg

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
                user_name=cfg.get("user_name") or None,
                user_address_as=cfg.get("user_address_as") or "none",
                user_title=cfg.get("user_title") or None,
            )
            yaml_text = render_config(answers)
            Config.model_validate(yaml.safe_load(yaml_text))  # validation
        except Exception as exc:
            return {"ok": False, "errors": [str(exc)]}

        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._env_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(yaml_text)

        # Determine which secret to write. Empty input + existing key = preserve.
        secret = cfg.get("_secret") or ""
        if not secret and provider == "ollama":
            secret = cfg.get("ollama_base_url") or "http://localhost:11434"
        if secret:
            existing = self._env_path.read_text() if self._env_path.exists() else ""
            self._env_path.write_text(render_env(provider, secret, existing=existing))
            try:
                self._env_path.chmod(0o600)
            except OSError:
                pass

        # Reload .env into the running process so new keys take effect immediately.
        try:
            from dotenv import load_dotenv
            load_dotenv(self._env_path, override=True)
        except Exception:
            log.exception("failed to reload .env")

        # Tell the orchestrator to swap brains for the new provider/model.
        if self._on_config_reload is not None:
            try:
                self._on_config_reload()
            except Exception:
                log.exception("config reload callback failed")

        # Emit fresh config event so the UI re-renders (with new has_secret).
        new_cfg = _config_to_dict(self._config_path) or _default_config_dict()
        new_cfg["has_secret"] = _has_secret_for(new_cfg["provider"], self._env_path)
        new_cfg["available_models"] = {p: list(m) for p, m in MODELS_BY_PROVIDER.items()}
        self._bus.publish({"type": "config", "cfg": new_cfg})
        return {"ok": True}

    def get_history(self) -> list[dict[str, Any]]:
        """Return the last 50 conversation history items for GUI replay."""
        if self._history is None:
            return []
        return self._history.load_recent(50)

    def quit(self) -> None:
        # Window close is handled in window.py; this is a hook for the JS quit shortcut.
        pass
