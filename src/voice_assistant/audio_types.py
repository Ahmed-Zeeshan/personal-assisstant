"""Audio data types shared between capture (audio_input) and STT (stt)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class AudioBuffer:
    """Mono float32 PCM samples in [-1, 1] at the given sample rate."""
    samples: np.ndarray
    sample_rate: int
