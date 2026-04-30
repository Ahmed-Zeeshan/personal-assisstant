# tests/test_setup_wizard.py
import sys
from pathlib import Path

import pytest
import yaml

from voice_assistant.config import Config
from voice_assistant.setup_wizard import (
    PROVIDER_ENV_VAR,
    WizardAnswers,
    render_config,
    render_env,
    run_wizard,
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


def _patch_io(monkeypatch, inputs: list[str], passwords: list[str]):
    input_iter = iter(inputs)
    pw_iter = iter(passwords)
    monkeypatch.setattr("builtins.input", lambda *_: next(input_iter))
    monkeypatch.setattr("getpass.getpass", lambda *_: next(pw_iter))


def test_wizard_writes_anthropic_config_and_env(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    # Extra "" at end = identity question default (choice "4" = don't address)
    _patch_io(monkeypatch, inputs=["1", "", "", "", ""], passwords=["sk-ant-test"])
    run_wizard(config_path=config_path, env_path=env_path)

    assert config_path.exists()
    assert env_path.exists()
    assert "ANTHROPIC_API_KEY=sk-ant-test" in env_path.read_text()
    assert "provider: anthropic" in config_path.read_text()


def test_wizard_writes_ollama_with_base_url_and_no_key(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    # Extra "" at end = identity question default
    _patch_io(monkeypatch, inputs=["4", "", "", "", "", ""], passwords=[])
    run_wizard(config_path=config_path, env_path=env_path)

    assert "OLLAMA_BASE_URL=http://localhost:11434" in env_path.read_text()
    assert "provider: ollama" in config_path.read_text()


def test_wizard_aborts_on_existing_config_when_user_declines(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    config_path.write_text("# existing\n")
    _patch_io(monkeypatch, inputs=["n"], passwords=[])
    run_wizard(config_path=config_path, env_path=env_path)

    assert config_path.read_text() == "# existing\n"
    assert not env_path.exists()


def test_wizard_force_overwrites_existing(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    config_path.write_text("# existing\n")
    # Extra "" at end = identity question default
    _patch_io(monkeypatch, inputs=["1", "", "", "", ""], passwords=["sk-ant-test"])
    run_wizard(config_path=config_path, env_path=env_path, force=True)

    assert "provider: anthropic" in config_path.read_text()


def test_wizard_writes_env_with_mode_0600(tmp_path, monkeypatch):
    if sys.platform == "win32":
        pytest.skip("file modes are POSIX-only")
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    # Extra "" at end = identity question default
    _patch_io(monkeypatch, inputs=["1", "", "", "", ""], passwords=["sk-ant-test"])
    run_wizard(config_path=config_path, env_path=env_path)

    mode = oct(env_path.stat().st_mode & 0o777)
    assert mode == "0o600"




def test_cli_setup_flag_runs_wizard(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    # Extra "" at end = identity question default
    inputs = iter(["1", "", "", "", ""])
    passwords = iter(["sk-ant-test"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda *_: next(passwords))
    monkeypatch.setattr(
        "voice_assistant.setup_wizard.run_wizard",
        lambda **kw: run_wizard(config_path=config_path, env_path=env_path, force=True),
    )
    monkeypatch.setattr("sys.argv", ["voice-assistant", "--setup", "--force"])

    from voice_assistant.cli import main
    main()

    assert config_path.exists()
    assert env_path.exists()
