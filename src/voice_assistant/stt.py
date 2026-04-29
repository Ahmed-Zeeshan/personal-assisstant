from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from faster_whisper import WhisperModel


@dataclass
class AudioBuffer:
    samples: np.ndarray   # mono float32 in [-1, 1]
    sample_rate: int


class Transcriber:
    def __init__(self, model_name: str = "small", device: str = "cpu") -> None:
        self.model = WhisperModel(
            model_name, device=device, compute_type="int8"
        )

    def transcribe(self, audio: AudioBuffer) -> str:
        if audio.sample_rate != 16000:
            raise ValueError(
                f"expected 16kHz audio, got {audio.sample_rate}"
            )
        segments, _info = self.model.transcribe(audio.samples, language="en")
        return " ".join(seg.text.strip() for seg in segments).strip()
