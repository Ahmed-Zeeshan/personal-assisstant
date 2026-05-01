from pathlib import Path

import pytest
import yaml

from voice_assistant.config import Config
from voice_assistant.setup_wizard import WizardAnswers, render_config


def _ans(**overrides):
    base = dict(
        provider="anthropic", model="claude-sonnet-4-6",
        hotkey="ctrl+shift+space",
        allowed_roots=[Path("~")],
        ollama_base_url=None,
        user_name=None, user_address_as="none", user_title=None,
        voice="piper:en_US-amy-medium", stt_language="auto", avatar="aria",
    )
    base.update(overrides)
    return WizardAnswers(**base)


def test_render_config_with_first_name():
    yaml_text = render_config(_ans(user_name="Zeeshan", user_address_as="first_name"))
    cfg = Config.model_validate(yaml.safe_load(yaml_text))
    assert cfg.user.name == "Zeeshan"
    assert cfg.user.address_as == "first_name"


def test_render_config_with_title():
    yaml_text = render_config(_ans(user_name="Zeeshan", user_address_as="title", user_title="Sir"))
    cfg = Config.model_validate(yaml.safe_load(yaml_text))
    assert cfg.user.address_as == "title"
    assert cfg.user.title == "Sir"


def test_user_config_defaults_when_omitted():
    """Configs predating identity (no user: block) must still validate."""
    yaml_text = """
brain: { provider: anthropic, model: claude-sonnet-4-6 }
stt:   { engine: faster-whisper, model: small, language: en }
tts:   { engine: piper, voice: en_US-amy-medium }
audio: { trigger: hotkey, hotkey: ctrl+shift+space, silence_seconds: 1.5 }
safety: { allowed_roots: ["~"], destructive_requires_confirmation: true, delete_rate_per_minute: 5 }
logging: { level: INFO, file: /tmp/x.log }
"""
    cfg = Config.model_validate(yaml.safe_load(yaml_text))
    assert cfg.user.name is None
    assert cfg.user.address_as == "none"


def test_render_config_includes_voice_and_stt_language():
    yaml_text = render_config(_ans(voice="openai:nova", stt_language="ur"))
    cfg = Config.model_validate(yaml.safe_load(yaml_text))
    assert cfg.tts.voice == "openai:nova"
    assert cfg.stt.language == "ur"


def test_render_config_respond_in_auto_omitted():
    """respond_in=auto should not write a user block just for respond_in."""
    yaml_text = render_config(_ans(respond_in="auto"))
    # No user block needed since name/address_as/respond_in all default
    cfg = Config.model_validate(yaml.safe_load(yaml_text))
    assert cfg.user.respond_in == "auto"


def test_render_config_respond_in_written_when_set():
    yaml_text = render_config(_ans(user_name="Zeeshan", user_address_as="first_name", respond_in="ur"))
    cfg = Config.model_validate(yaml.safe_load(yaml_text))
    assert cfg.user.respond_in == "ur"


def test_user_config_respond_in_defaults_to_auto():
    """Old configs without respond_in field must still parse."""
    yaml_text = """
brain: { provider: anthropic, model: claude-sonnet-4-6 }
stt:   { engine: faster-whisper, model: small, language: en }
tts:   { engine: piper, voice: en_US-amy-medium }
audio: { trigger: hotkey, hotkey: ctrl+shift+space, silence_seconds: 1.5 }
safety: { allowed_roots: ["~"], destructive_requires_confirmation: true, delete_rate_per_minute: 5 }
logging: { level: INFO, file: /tmp/x.log }
user:  { name: Alice, address_as: first_name }
"""
    cfg = Config.model_validate(yaml.safe_load(yaml_text))
    assert cfg.user.respond_in == "auto"


def test_render_config_audio_wake_word_fields_round_trip():
    yaml_text = render_config(_ans(audio_trigger="wake_word", wake_word="alexa", wake_sensitivity=0.7))
    cfg = Config.model_validate(yaml.safe_load(yaml_text))
    assert cfg.audio.trigger == "wake_word"
    assert cfg.audio.wake_word == "alexa"
    assert cfg.audio.wake_sensitivity == pytest.approx(0.7)


def test_audio_config_defaults_backward_compat():
    """Old configs with only trigger/hotkey/silence_seconds must still validate."""
    yaml_text = """
brain: { provider: anthropic, model: claude-sonnet-4-6 }
stt:   { engine: faster-whisper, model: small, language: en }
tts:   { engine: piper, voice: en_US-amy-medium }
audio: { trigger: hotkey, hotkey: ctrl+shift+space, silence_seconds: 1.5 }
safety: { allowed_roots: ["~"], destructive_requires_confirmation: true, delete_rate_per_minute: 5 }
logging: { level: INFO, file: /tmp/x.log }
"""
    cfg = Config.model_validate(yaml.safe_load(yaml_text))
    assert cfg.audio.wake_word == "hey_jarvis"
    assert cfg.audio.wake_sensitivity == 0.5
