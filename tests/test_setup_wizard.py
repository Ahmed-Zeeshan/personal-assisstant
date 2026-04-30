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
