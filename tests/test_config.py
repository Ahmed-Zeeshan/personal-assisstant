from pathlib import Path
import textwrap
import pytest
from voice_assistant.config import load_config, Config


def write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(body))
    return p


def test_load_minimal_valid_config(tmp_path: Path):
    cfg_path = write(
        tmp_path,
        """
        brain:
          provider: claude
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
    assert cfg.brain.provider == "claude"
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
        brain: {provider: claude, model: claude-sonnet-4-6}
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
