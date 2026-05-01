"""TTS factory: pick engine based on voice id."""

from __future__ import annotations

from voice_assistant.tts.base import Speaker
from voice_assistant.voice_catalog import find_voice


def make_speaker(*, voice_id: str, speed: float = 1.15) -> Speaker:
    """Construct the appropriate Speaker for the given voice id.

    voice_id has the form 'engine:name' — e.g. 'piper:en_US-amy-medium', 'openai:nova'.
    speed: speech rate multiplier (0.5 slow … 2.0 fast; default 1.15 is natural-fast).
    """
    if ":" not in voice_id:
        # Legacy: bare piper voice
        voice_id = f"piper:{voice_id}"

    voice = find_voice(voice_id)
    if voice is None:
        raise ValueError(f"unknown voice id: {voice_id!r}")

    engine, name = voice_id.split(":", 1)
    if engine == "piper":
        from voice_assistant.tts.piper_engine import PiperSpeaker

        return PiperSpeaker(voice=name, speed=speed)
    if engine == "openai":
        from voice_assistant.tts.openai_engine import OpenAISpeaker

        return OpenAISpeaker(voice=name, speed=speed)
    raise ValueError(f"unknown TTS engine: {engine!r}")


__all__ = ["Speaker", "make_speaker"]
