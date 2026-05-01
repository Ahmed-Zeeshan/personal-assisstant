"""TTS factory: pick engine based on voice id."""
from __future__ import annotations

from voice_assistant.tts.base import Speaker
from voice_assistant.voice_catalog import find_voice


def make_speaker(*, voice_id: str) -> Speaker:
    """Construct the appropriate Speaker for the given voice id.

    voice_id has the form 'engine:name' — e.g. 'piper:en_US-amy-medium', 'openai:nova'.
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
        return PiperSpeaker(voice=name)
    if engine == "openai":
        from voice_assistant.tts.openai_engine import OpenAISpeaker
        return OpenAISpeaker(voice=name)
    raise ValueError(f"unknown TTS engine: {engine!r}")


__all__ = ["Speaker", "make_speaker"]
