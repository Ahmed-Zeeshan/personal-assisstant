from __future__ import annotations

import os

import pytest

from voice_assistant.desktop.bridge import Bridge
from voice_assistant.desktop.events import EventBus


@pytest.fixture
def tmp_paths(tmp_path):
    return tmp_path / "config.yaml", tmp_path / ".env"


@pytest.fixture
def bridge_with_config(tmp_paths):
    cfg_path, env_path = tmp_paths
    bus = EventBus()
    sent: list[tuple[str, list[str]]] = []
    bridge = Bridge(
        config_path=cfg_path,
        env_path=env_path,
        bus=bus,
        on_send_text=lambda t, imgs: sent.append((t, imgs)),
        on_listening_start=lambda: None,
        on_listening_stop=lambda: None,
    )
    return bridge, bus, sent, cfg_path, env_path


def test_bridge_send_text_invokes_callback(bridge_with_config):
    bridge, _, sent, _, _ = bridge_with_config
    bridge.send_text("hello")
    assert sent == [("hello", [])]


def test_bridge_get_config_returns_default_shape_when_missing(bridge_with_config):
    bridge, _, _, _, _ = bridge_with_config
    cfg = bridge.get_config()
    assert cfg["provider"] in ("anthropic", "openai", "gemini", "ollama")
    assert isinstance(cfg["model"], str) and cfg["model"]
    assert isinstance(cfg["hotkey"], str)
    assert isinstance(cfg["allowed_roots"], list)


def test_bridge_save_config_writes_files_and_strips_stale_keys(bridge_with_config):
    bridge, _, _, cfg_path, env_path = bridge_with_config
    env_path.write_text("ANTHROPIC_API_KEY=old\nFOO=bar\n")
    result = bridge.save_config(
        {
            "provider": "openai",
            "model": "gpt-4o",
            "hotkey": "ctrl+shift+space",
            "allowed_roots": ["~"],
            "ollama_base_url": None,
            "_secret": "sk-new",
        }
    )
    assert result == {"ok": True}
    assert cfg_path.exists()
    env_text = env_path.read_text()
    assert "OPENAI_API_KEY=sk-new" in env_text
    assert "ANTHROPIC_API_KEY" not in env_text
    assert "FOO=bar" in env_text


def test_bridge_save_config_validation_failure_returns_errors(bridge_with_config):
    bridge, _, _, cfg_path, _ = bridge_with_config
    result = bridge.save_config(
        {
            "provider": "nonexistent",
            "model": "x",
            "hotkey": "x",
            "allowed_roots": ["~"],
            "ollama_base_url": None,
            "_secret": "k",
        }
    )
    assert result["ok"] is False
    assert isinstance(result["errors"], list) and result["errors"]
    assert not cfg_path.exists()


def test_bridge_save_config_emits_config_event(bridge_with_config):
    bridge, bus, _, _, _ = bridge_with_config
    seen: list[dict] = []
    bus.subscribe(lambda e: seen.append(e) if e.get("type") == "config" else None)
    bridge.save_config(
        {
            "provider": "anthropic",
            "model": "claude-sonnet-4-6",
            "hotkey": "ctrl+shift+space",
            "allowed_roots": ["~"],
            "ollama_base_url": None,
            "_secret": "sk-ant-test",
        }
    )
    assert len(seen) == 1
    assert seen[0]["cfg"]["provider"] == "anthropic"


def test_bridge_save_config_persists_voice_avatar_stt(bridge_with_config):
    """voice/avatar/stt_language must round-trip through save_config → get_config."""
    bridge, _, _, _cfg_path, _ = bridge_with_config
    bridge.save_config(
        {
            "provider": "anthropic",
            "model": "claude-sonnet-4-6",
            "hotkey": "ctrl+shift+space",
            "allowed_roots": ["~"],
            "ollama_base_url": None,
            "_secret": "sk-ant-test",
            "voice": "openai:nova",
            "stt_language": "ur",
            "avatar": "liam",
            "respond_in": "ur",
        }
    )
    result = bridge.get_config()
    assert result["voice"] == "openai:nova"
    assert result["stt_language"] == "ur"
    assert result["avatar"] == "liam"
    assert result["respond_in"] == "ur"


def test_bridge_save_config_persists_wake_word_fields(bridge_with_config):
    bridge, _, _, _cfg_path, _ = bridge_with_config
    bridge.save_config(
        {
            "provider": "anthropic",
            "model": "claude-sonnet-4-6",
            "hotkey": "ctrl+shift+space",
            "allowed_roots": ["~"],
            "ollama_base_url": None,
            "_secret": "sk-ant-test",
            "audio_trigger": "wake_word",
            "wake_word": "alexa",
            "wake_sensitivity": 0.8,
        }
    )
    result = bridge.get_config()
    assert result["audio_trigger"] == "wake_word"
    assert result["wake_word"] == "alexa"
    assert abs(result["wake_sensitivity"] - 0.8) < 1e-6


def test_bridge_save_config_persists_tts_speed(bridge_with_config):
    """tts_speed must round-trip through save_config → get_config."""
    bridge, _, _, _cfg_path, _ = bridge_with_config
    bridge.save_config(
        {
            "provider": "anthropic",
            "model": "claude-sonnet-4-6",
            "hotkey": "ctrl+shift+space",
            "allowed_roots": ["~"],
            "ollama_base_url": None,
            "_secret": "sk-ant-test",
            "tts_speed": 1.3,
        }
    )
    result = bridge.get_config()
    assert abs(result["tts_speed"] - 1.3) < 1e-6


def test_bridge_env_file_is_mode_0600(bridge_with_config):
    if os.name == "nt":
        pytest.skip("file modes are POSIX-only")
    bridge, _, _, _, env_path = bridge_with_config
    bridge.save_config(
        {
            "provider": "anthropic",
            "model": "claude-sonnet-4-6",
            "hotkey": "ctrl+shift+space",
            "allowed_roots": ["~"],
            "ollama_base_url": None,
            "_secret": "sk-ant-test",
        }
    )
    assert oct(env_path.stat().st_mode & 0o777) == "0o600"
