import textwrap
from pathlib import Path

import pytest

from voice_assistant.config import Config, load_config


def write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(body))
    return p


def test_load_minimal_valid_config(tmp_path: Path):
    cfg_path = write(
        tmp_path,
        """
        brain:
          provider: anthropic
          model: claude-sonnet-4-6
        stt:
          engine: faster-whisper
          model: small
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
          file: logs/voice-assistant.log
        """,
    )
    cfg = load_config(cfg_path)
    assert isinstance(cfg, Config)
    assert cfg.brain.provider == "anthropic"
    assert cfg.brain.model == "claude-sonnet-4-6"
    assert cfg.audio.silence_seconds == 1.5
    assert cfg.safety.delete_rate_per_minute == 5


def test_unknown_provider_rejected(tmp_path: Path):
    cfg_path = write(
        tmp_path,
        """
        brain:
          provider: bogus
          model: x
        stt: {engine: faster-whisper, model: small}
        tts: {engine: piper, voice: x}
        audio: {trigger: hotkey, hotkey: x, silence_seconds: 1.0}
        safety: {allowed_roots: ["~"], destructive_requires_confirmation: true, delete_rate_per_minute: 5}
        gmail: {credentials_file: x}
        logging: {level: INFO, file: x}
        """,
    )
    with pytest.raises(ValueError):
        load_config(cfg_path)


def test_allowed_roots_expand_user(tmp_path: Path):
    cfg_path = write(
        tmp_path,
        """
        brain: {provider: anthropic, model: claude-sonnet-4-6}
        stt: {engine: faster-whisper, model: small}
        tts: {engine: piper, voice: en_US-amy-medium}
        audio: {trigger: hotkey, hotkey: ctrl+shift+space, silence_seconds: 1.5}
        safety:
          allowed_roots: ["~"]
          destructive_requires_confirmation: true
          delete_rate_per_minute: 5
        gmail: {credentials_file: ~/.voice-assistant/gmail-creds.json}
        logging: {level: INFO, file: logs/voice-assistant.log}
        """,
    )
    cfg = load_config(cfg_path)
    assert cfg.safety.allowed_roots[0].is_absolute()


def test_missing_config_file_raises_clear_error(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="not found"):
        load_config(tmp_path / "does-not-exist.yaml")


def test_malformed_yaml_raises_value_error(tmp_path: Path):
    bad = tmp_path / "config.yaml"
    bad.write_text("brain: { unclosed")
    with pytest.raises(ValueError, match="Malformed YAML"):
        load_config(bad)


def test_tts_speed_defaults_to_1_15(tmp_path: Path):
    cfg_path = write(
        tmp_path,
        """
        brain: {provider: anthropic, model: claude-sonnet-4-6}
        stt: {engine: faster-whisper, model: small}
        tts: {engine: piper, voice: en_US-amy-medium}
        audio: {trigger: hotkey, hotkey: ctrl+shift+space, silence_seconds: 1.5}
        safety:
          allowed_roots: ["~"]
          destructive_requires_confirmation: true
          delete_rate_per_minute: 5
        logging: {level: INFO, file: logs/voice-assistant.log}
        """,
    )
    cfg = load_config(cfg_path)
    assert cfg.tts.speed == 1.15


def test_tts_speed_custom_value(tmp_path: Path):
    cfg_path = write(
        tmp_path,
        """
        brain: {provider: anthropic, model: claude-sonnet-4-6}
        stt: {engine: faster-whisper, model: small}
        tts: {engine: piper, voice: en_US-amy-medium, speed: 1.3}
        audio: {trigger: hotkey, hotkey: ctrl+shift+space, silence_seconds: 1.5}
        safety:
          allowed_roots: ["~"]
          destructive_requires_confirmation: true
          delete_rate_per_minute: 5
        logging: {level: INFO, file: logs/voice-assistant.log}
        """,
    )
    cfg = load_config(cfg_path)
    assert cfg.tts.speed == pytest.approx(1.3)


def test_tts_speed_out_of_range_rejected(tmp_path: Path):
    cfg_path = write(
        tmp_path,
        """
        brain: {provider: anthropic, model: claude-sonnet-4-6}
        stt: {engine: faster-whisper, model: small}
        tts: {engine: piper, voice: en_US-amy-medium, speed: 3.0}
        audio: {trigger: hotkey, hotkey: ctrl+shift+space, silence_seconds: 1.5}
        safety:
          allowed_roots: ["~"]
          destructive_requires_confirmation: true
          delete_rate_per_minute: 5
        logging: {level: INFO, file: logs/voice-assistant.log}
        """,
    )
    with pytest.raises(ValueError):
        load_config(cfg_path)


def test_gmail_section_is_optional(tmp_path: Path):
    cfg_path = write(
        tmp_path,
        """
        brain: {provider: anthropic, model: claude-sonnet-4-6}
        stt: {engine: faster-whisper, model: small}
        tts: {engine: piper, voice: en_US-amy-medium}
        audio: {trigger: hotkey, hotkey: ctrl+shift+space, silence_seconds: 1.5}
        safety:
          allowed_roots: ["~"]
          destructive_requires_confirmation: true
          delete_rate_per_minute: 5
        logging: {level: INFO, file: logs/voice-assistant.log}
        """,
    )
    cfg = load_config(cfg_path)
    assert cfg.gmail is None
