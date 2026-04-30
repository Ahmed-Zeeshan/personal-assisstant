from pathlib import Path

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
