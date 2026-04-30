# tests/test_setup_wizard.py
from pathlib import Path
import yaml
from voice_assistant.setup_wizard import WizardAnswers, render_config
from voice_assistant.config import Config
from voice_assistant.setup_wizard import (
    PROVIDER_ENV_VAR,
    render_env,
)


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


def test_render_env_for_each_provider_writes_correct_key():
    for provider, expected_var in PROVIDER_ENV_VAR.items():
        env = render_env(provider, "secret-value", existing="")
        assert f"{expected_var}=secret-value" in env


def test_render_env_strips_other_provider_keys():
    existing = (
        "ANTHROPIC_API_KEY=old-anthropic-key\n"
        "OPENAI_API_KEY=old-openai-key\n"
        "FOO=bar\n"
    )
    env = render_env("gemini", "new-gemini-key", existing=existing)
    assert "ANTHROPIC_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "GEMINI_API_KEY=new-gemini-key" in env
    assert "FOO=bar" in env  # unrelated keys preserved


def test_render_env_for_ollama_writes_base_url():
    env = render_env("ollama", "http://localhost:11434", existing="")
    assert "OLLAMA_BASE_URL=http://localhost:11434" in env
    assert "ANTHROPIC_API_KEY" not in env
