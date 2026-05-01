"""Local speech-to-text wrapper around faster-whisper.

Inputs are required to be mono float32 PCM samples in [-1, 1] at 16 kHz.
This contract is enforced at the AudioBuffer boundary so silent
miscompiled audio cannot reach the model.
"""

from __future__ import annotations

import logging

import numpy as np
from faster_whisper import WhisperModel

from voice_assistant.audio_types import AudioBuffer

log = logging.getLogger(__name__)


class Transcriber:
    def __init__(
        self,
        model_name: str = "small",
        device: str = "cpu",
        language: str = "en",
    ) -> None:
        self.language = language
        compute_type = "int8" if device == "cpu" else "float16"
        try:
            self.model = WhisperModel(model_name, device=device, compute_type=compute_type)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load WhisperModel '{model_name}' on device "
                f"'{device}' (compute_type={compute_type}): {exc}"
            ) from exc

    def transcribe(self, audio: AudioBuffer) -> str:
        if audio.sample_rate != 16000:
            raise ValueError(f"expected 16kHz audio, got {audio.sample_rate}")
        if audio.samples.ndim != 1:
            raise ValueError(f"expected mono (1-D) audio, got shape {audio.samples.shape}")
        if audio.samples.dtype != np.float32:
            raise ValueError(f"expected float32 samples, got {audio.samples.dtype}")
        if audio.samples.size == 0:
            return ""
        segments, info = self.model.transcribe(audio.samples, language=self.language)
        log.debug(
            "stt: language_probability=%.3f duration=%.2fs",
            getattr(info, "language_probability", 0.0),
            getattr(info, "duration", 0.0),
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
