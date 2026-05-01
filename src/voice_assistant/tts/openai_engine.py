"""OpenAI TTS engine. Uses gpt-4o-mini-tts for premium multilingual voices.

Streams audio bytes from the OpenAI API and plays via sounddevice.
"""

from __future__ import annotations

import io
import logging
import os

from voice_assistant.tts.base import Speaker

log = logging.getLogger(__name__)


class OpenAISpeaker(Speaker):
    """OpenAI TTS. Voice id is bare (e.g. 'nova'), not prefixed."""

    def __init__(self, voice: str, model: str = "gpt-4o-mini-tts") -> None:
        self._voice = voice
        self._model = model
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY not set; OpenAI TTS requires an API key. "
                "Set it via the wizard or settings drawer."
            )

    def speak(self, text: str) -> None:
        if not text.strip():
            return
        try:
            import sounddevice as sd
            import soundfile as sf  # type: ignore[import-not-found]
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI TTS dependencies missing. Install with: pip install openai soundfile"
            ) from exc

        client = OpenAI()
        # response_format=wav so soundfile/sounddevice can play directly.
        with client.audio.speech.with_streaming_response.create(
            model=self._model,
            voice=self._voice,
            input=text,
            response_format="wav",
        ) as response:
            buf = io.BytesIO()
            for chunk in response.iter_bytes():
                buf.write(chunk)
            buf.seek(0)
            data, samplerate = sf.read(buf, dtype="float32")
            sd.play(data, samplerate)
            sd.wait()
