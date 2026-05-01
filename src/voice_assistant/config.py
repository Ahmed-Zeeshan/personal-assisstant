from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class BrainConfig(BaseModel):
    provider: Literal["anthropic", "openai", "gemini", "ollama"]
    model: str


class UserConfig(BaseModel):
    name: str | None = None
    address_as: Literal["first_name", "full_name", "title", "none"] = "none"
    title: str | None = None
    respond_in: str = "auto"  # "auto" or ISO language code e.g. "ur", "hi", "cs"


class STTConfig(BaseModel):
    engine: Literal["faster-whisper"] = "faster-whisper"
    model: str = "small"
    language: str = "auto"  # "auto" or ISO 639-1 code


class TTSConfig(BaseModel):
    engine: Literal["piper", "openai", "elevenlabs"] = "piper"
    voice: str = "piper:en_US-amy-medium"  # full id from the catalog
    speed: float = 1.15  # speech rate: 0.5 (slow) … 2.0 (fast); default is natural-fast

    @field_validator("voice")
    @classmethod
    def _check_voice_id(cls, v: str) -> str:
        # Allow either bare piper voice (legacy: "en_US-amy-medium") or prefixed.
        if ":" not in v:
            return f"piper:{v}"
        return v

    @field_validator("speed")
    @classmethod
    def _check_speed(cls, v: float) -> float:
        if not (0.5 <= v <= 2.0):
            raise ValueError(f"tts.speed must be between 0.5 and 2.0, got {v}")
        return v


class AudioConfig(BaseModel):
    trigger: Literal["hotkey", "wake_word"] = "hotkey"
    hotkey: str = "ctrl+shift+space"
    silence_seconds: float = Field(default=1.5, gt=0)
    wake_word: str = "hey_jarvis"
    wake_sensitivity: float = 0.5


class SafetyConfig(BaseModel):
    allowed_roots: list[Path]
    destructive_requires_confirmation: bool
    delete_rate_per_minute: int = Field(ge=0)

    @field_validator("allowed_roots")
    @classmethod
    def expand_roots(cls, v: list[Path]) -> list[Path]:
        return [p.expanduser().resolve() for p in v]


class GmailConfig(BaseModel):
    credentials_file: Path

    @field_validator("credentials_file")
    @classmethod
    def expand(cls, v: Path) -> Path:
        return v.expanduser()


class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    file: Path


class SecurityConfig(BaseModel):
    """Optional at-rest encryption for sensitive user data files."""

    encrypt_user_data: bool = False


class DisplayConfig(BaseModel):
    """Display preferences (high-contrast theme, font size)."""

    theme: Literal["default", "hc"] = "default"
    font_size: Literal["small", "medium", "large", "xl"] = "medium"


class Config(BaseModel):
    brain: BrainConfig
    stt: STTConfig
    tts: TTSConfig
    audio: AudioConfig
    safety: SafetyConfig
    gmail: GmailConfig | None = None
    logging: LoggingConfig
    user: UserConfig = Field(default_factory=UserConfig)
    avatar: str = Field(default="aria")  # UI metadata: aria | liam | sage
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    locale: str = "auto"  # "auto" or BCP-47 language code e.g. "en", "ur", "hi"
    transparency_acknowledged: bool = False  # AI Act first-run disclosure
    onboarding_seen: bool = False  # first-run onboarding tour


def load_config(path: Path) -> Config:
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text())
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {path}") from None
    except yaml.YAMLError as e:
        raise ValueError(f"Malformed YAML in {path}: {e}") from e
    try:
        return Config.model_validate(raw)
    except ValidationError as e:
        raise ValueError(f"Invalid config at {path}: {e}") from e
