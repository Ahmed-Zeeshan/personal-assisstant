from __future__ import annotations
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class BrainConfig(BaseModel):
    provider: Literal["claude", "openai", "gemini", "ollama"]
    model: str


class STTConfig(BaseModel):
    engine: Literal["faster-whisper"]
    model: str


class TTSConfig(BaseModel):
    engine: Literal["piper", "elevenlabs"]
    voice: str


class AudioConfig(BaseModel):
    trigger: Literal["hotkey", "wake_word"]
    hotkey: str
    silence_seconds: float = Field(gt=0)


class SafetyConfig(BaseModel):
    allowed_roots: list[Path]
    destructive_requires_confirmation: bool
    delete_rate_per_minute: int = Field(ge=0)

    @field_validator("allowed_roots")
    @classmethod
    def expand_roots(cls, v: list[Path]) -> list[Path]:
        return [Path(str(p)).expanduser().resolve() for p in v]


class GmailConfig(BaseModel):
    credentials_file: Path

    @field_validator("credentials_file")
    @classmethod
    def expand(cls, v: Path) -> Path:
        return Path(str(v)).expanduser()


class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    file: Path


class Config(BaseModel):
    brain: BrainConfig
    stt: STTConfig
    tts: TTSConfig
    audio: AudioConfig
    safety: SafetyConfig
    gmail: GmailConfig
    logging: LoggingConfig


def load_config(path: Path) -> Config:
    raw = yaml.safe_load(Path(path).read_text())
    try:
        return Config.model_validate(raw)
    except ValidationError as e:
        raise ValueError(f"Invalid config at {path}: {e}") from e
