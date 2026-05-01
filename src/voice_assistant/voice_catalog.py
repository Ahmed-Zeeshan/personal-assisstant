"""Single source of truth for available TTS voices.

Each voice has:
  id        — engine-prefixed unique key, e.g. "openai:nova" or "piper:en_US-amy-medium"
  label     — human-readable display name
  language  — ISO 639-1 (e.g. "en", "ur", "hi")
  gender    — "female" | "male" | "neutral"
  engine    — "piper" | "openai"
  notes     — optional, shown as small text in the UI
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Voice:
    id: str
    label: str
    language: str
    gender: Literal["female", "male", "neutral"]
    engine: Literal["piper", "openai"]
    notes: str = ""


# OpenAI TTS — gpt-4o-mini-tts model supports 50+ languages with the same voice.
# Listed languages are the primary UI categorisations; the voice itself works for
# all supported languages of the underlying model.
_OPENAI_VOICES = [
    ("alloy",   "Alloy — neutral, calm",       "neutral"),
    ("echo",    "Echo — warm, male",           "male"),
    ("fable",   "Fable — British, male",       "male"),
    ("onyx",    "Onyx — deep, male",           "male"),
    ("nova",    "Nova — friendly, female",     "female"),
    ("shimmer", "Shimmer — bright, female",    "female"),
    ("coral",   "Coral — gentle, female",      "female"),
    ("sage",    "Sage — measured, neutral",    "neutral"),
    ("ash",     "Ash — confident, male",       "male"),
    ("ballad",  "Ballad — expressive, female", "female"),
]
_OPENAI_LANGUAGES = [
    ("en", "English"), ("ur", "Urdu"), ("hi", "Hindi"),
    ("ar", "Arabic"), ("zh", "Chinese"), ("ja", "Japanese"), ("ko", "Korean"),
    ("de", "German"), ("fr", "French"), ("es", "Spanish"), ("it", "Italian"),
    ("pt", "Portuguese"), ("ru", "Russian"), ("nl", "Dutch"), ("pl", "Polish"),
    ("cs", "Czech"), ("sk", "Slovak"), ("hu", "Hungarian"), ("ro", "Romanian"),
    ("tr", "Turkish"), ("uk", "Ukrainian"), ("el", "Greek"), ("sv", "Swedish"),
    ("da", "Danish"), ("no", "Norwegian"), ("fi", "Finnish"), ("bg", "Bulgarian"),
    ("hr", "Croatian"), ("sr", "Serbian"), ("vi", "Vietnamese"), ("id", "Indonesian"),
    ("th", "Thai"), ("he", "Hebrew"), ("fa", "Persian"),
]

_PIPER_VOICES = [
    # English (offline, fast — default)
    ("en_US-amy-medium",        "Amy — US English (default)",    "en", "female"),
    ("en_US-ryan-medium",       "Ryan — US English",             "en", "male"),
    ("en_US-libritts-high",     "LibriTTS HQ — US English",      "en", "neutral"),
    ("en_GB-alan-medium",       "Alan — UK English",             "en", "male"),
    ("en_GB-jenny_dioco-medium", "Jenny — UK English",           "en", "female"),
]

VOICES: list[Voice] = []

# OpenAI: each voice x each language is one VOICES entry. The id stays voice-only;
# `language` is metadata used for filtering. The OpenAI TTS engine ignores language
# (the model auto-detects); we only use it to group in the UI.
for lang, lang_label in _OPENAI_LANGUAGES:
    for vid, vlabel, vgender in _OPENAI_VOICES:
        VOICES.append(Voice(
            id=f"openai:{vid}",
            label=f"{vlabel} ({lang_label})" if lang != "en" else vlabel,
            language=lang,
            gender=vgender,  # type: ignore[arg-type]
            engine="openai",
            notes="online · OpenAI · multilingual",
        ))

for vid, vlabel, vlang, vgender in _PIPER_VOICES:
    VOICES.append(Voice(
        id=f"piper:{vid}",
        label=vlabel,
        language=vlang,
        gender=vgender,  # type: ignore[arg-type]
        engine="piper",
        notes="offline · Piper",
    ))


def voices_for(*, language: str | None = None, engine: str | None = None) -> list[Voice]:
    out = VOICES
    if language is not None:
        out = [v for v in out if v.language == language]
    if engine is not None:
        out = [v for v in out if v.engine == engine]
    return out


def find_voice(voice_id: str) -> Voice | None:
    for v in VOICES:
        if v.id == voice_id:
            return v
    return None


# A short list of STT languages exposed in the UI (faster-whisper handles 99 — these
# are the user-friendly highlights).
STT_LANGUAGES: list[tuple[str, str]] = [
    ("auto", "Auto-detect"),
    ("en", "English"),
    ("ur", "Urdu"),
    ("hi", "Hindi"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("it", "Italian"),
    ("pt", "Portuguese"),
    ("ru", "Russian"),
    ("zh", "Chinese"),
    ("ja", "Japanese"),
    ("ar", "Arabic"),
    ("nl", "Dutch"),
    ("pl", "Polish"),
    ("cs", "Czech"),
    ("sk", "Slovak"),
    ("hu", "Hungarian"),
    ("ro", "Romanian"),
    ("tr", "Turkish"),
    ("uk", "Ukrainian"),
    ("el", "Greek"),
    ("sv", "Swedish"),
    ("fi", "Finnish"),
    ("no", "Norwegian"),
]
