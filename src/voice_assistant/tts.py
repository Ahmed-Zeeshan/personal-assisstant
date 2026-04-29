from __future__ import annotations
import wave
from pathlib import Path
import sounddevice as sd
import numpy as np
from piper.voice import PiperVoice
from piper.download_voices import download_voice

# Default cache directory for downloaded voice models
_CACHE_DIR = Path.home() / ".cache" / "piper"


class Speaker:
    def __init__(self, voice: str) -> None:
        # piper-tts 1.4.x requires an explicit model file path.
        # We download on first use into ~/.cache/piper.
        self._voice_name = voice
        model_path = _ensure_model(voice)
        self._voice = PiperVoice.load(model_path)

    def synthesise_to_file(self, text: str, out_path: Path) -> None:
        with wave.open(str(out_path), "wb") as wav_file:
            self._voice.synthesize_wav(text, wav_file)

    def speak(self, text: str) -> None:
        chunks = []
        for chunk in self._voice.synthesize(text):
            chunks.append(chunk.audio_int16_array)
        if not chunks:
            return
        audio = np.concatenate(chunks)
        sd.play(audio, samplerate=self._voice.config.sample_rate)
        sd.wait()


def _ensure_model(voice: str) -> Path:
    """Download voice model if not already cached; return path to .onnx file."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    model_path = _CACHE_DIR / f"{voice}.onnx"
    if not model_path.exists() or model_path.stat().st_size == 0:
        download_voice(voice, _CACHE_DIR)
    return model_path
