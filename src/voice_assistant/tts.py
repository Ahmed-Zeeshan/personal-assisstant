"""Local text-to-speech wrapper around piper-tts (v1.4.x API).

Voice models are cached at ~/.cache/piper. First use of a new voice
downloads both the .onnx model and the .onnx.json config.
"""
from __future__ import annotations

import logging
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
from piper.download_voices import download_voice
from piper.voice import PiperVoice

log = logging.getLogger(__name__)

_CACHE_DIR = Path.home() / ".cache" / "piper"


class Speaker:
    def __init__(self, voice: str) -> None:
        self._voice_name = voice
        model_path = _ensure_model(voice)
        log.debug("loading piper voice from %s", model_path)
        self._voice = PiperVoice.load(model_path)

    def synthesise_to_file(self, text: str, out_path: Path) -> None:
        if not text.strip():
            log.warning("synthesise_to_file called with empty text; skipping")
            return
        with wave.open(str(out_path), "wb") as wav_file:
            self._voice.synthesize_wav(text, wav_file)

    def speak(self, text: str) -> None:
        # NOTE: sd.play internally stops any prior playback. Concurrent calls
        # from multiple threads will truncate each other's audio. The
        # orchestrator is sequential, so this is acceptable for v1.
        if not text.strip():
            return
        chunks = []
        for chunk in self._voice.synthesize(text):
            chunks.append(chunk.audio_int16_array)
        if not chunks:
            return
        audio = np.concatenate(chunks)
        sd.play(audio, samplerate=self._voice.config.sample_rate)
        sd.wait()


def _ensure_model(voice: str) -> Path:
    """Download voice model if not already cached; return path to .onnx file.

    Validates BOTH the model (.onnx) and config (.onnx.json) so a partially
    downloaded voice is recovered cleanly.
    """
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    model_path = _CACHE_DIR / f"{voice}.onnx"
    config_path = _CACHE_DIR / f"{voice}.onnx.json"
    needs_download = (
        not model_path.exists() or model_path.stat().st_size == 0
        or not config_path.exists() or config_path.stat().st_size == 0
    )
    if needs_download:
        log.info("downloading piper voice %s to %s", voice, _CACHE_DIR)
        try:
            download_voice(voice, _CACHE_DIR)
        except ValueError as exc:
            raise ValueError(
                f"Invalid piper voice name {voice!r}. "
                f"Expected format: <lang_code>-<name>-<quality>, "
                f"e.g. 'en_US-amy-medium'. Original error: {exc}"
            ) from exc
        except OSError as exc:
            raise RuntimeError(
                f"Failed to download piper voice {voice!r} to {_CACHE_DIR}: {exc}"
            ) from exc
    return model_path
