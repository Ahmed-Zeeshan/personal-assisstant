"""Voice Activity Detection via Silero VAD (lazy import, optional dependency).

Usage
-----
    from voice_assistant.audio.vad import VoiceActivityDetector

    vad = VoiceActivityDetector()
    is_speech = vad.detect(chunk_16khz_bytes)

    # Or streaming with callback:
    vad.listen_async(on_speech_detected)

The module requires the ``vad`` optional-dependency group::

    pip install "voice-assistant[vad]"

If silero-vad is not installed, instantiating :class:`VoiceActivityDetector`
raises :class:`ImportError` with an instructive message.

Sample-rate: Silero VAD expects 16 000 Hz mono, 512-sample (32 ms) chunks.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

log = logging.getLogger(__name__)

# Chunk size in bytes: 512 samples x 2 bytes/sample (int16)
_CHUNK_BYTES = 512 * 2
_SAMPLE_RATE = 16_000


class VoiceActivityDetector:
    """Wraps the Silero VAD model for chunk-level speech detection.

    Parameters
    ----------
    threshold:
        Confidence threshold in [0, 1]. Values above this are speech.
    sample_rate:
        Audio sample rate in Hz. Silero supports 8000 or 16000.
    """

    def __init__(self, threshold: float = 0.5, sample_rate: int = _SAMPLE_RATE) -> None:
        try:
            import silero_vad  # noqa: F401
            import torch
        except ImportError as exc:
            raise ImportError(
                "silero-vad is required for VAD support. "
                'Install it with: pip install "voice-assistant[vad]"'
            ) from exc

        self._threshold = threshold
        self._sample_rate = sample_rate
        self._torch = torch

        # Load Silero VAD model (downloads on first use, then cached).
        model, _utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            trust_repo=True,
        )
        self._model = model
        self._model.eval()

    def detect(self, chunk: bytes) -> bool:
        """Return True if *chunk* contains voice activity.

        Parameters
        ----------
        chunk:
            Raw PCM bytes — 16-bit little-endian mono, at ``sample_rate`` Hz.
            Expected length: :data:`_CHUNK_BYTES` (512 samples / 32 ms at 16 kHz).
        """
        import struct

        # Convert PCM bytes → float32 tensor in [-1, 1]
        n_samples = len(chunk) // 2
        samples = struct.unpack(f"<{n_samples}h", chunk[: n_samples * 2])
        tensor = self._torch.tensor(samples, dtype=self._torch.float32) / 32768.0
        tensor = tensor.unsqueeze(0)  # shape: [1, n_samples]

        with self._torch.no_grad():
            confidence: float = self._model(tensor, self._sample_rate).item()

        return confidence >= self._threshold

    def listen_async(
        self,
        callback: Callable[[], None],
        *,
        stop_event: threading.Event | None = None,
    ) -> threading.Thread:
        """Start a background thread that calls *callback* when voice is detected.

        Parameters
        ----------
        callback:
            Zero-argument callable; invoked (in the listener thread) each time
            a chunk is classified as speech.
        stop_event:
            Optional :class:`threading.Event`; set it to stop the listener.

        Returns
        -------
        threading.Thread
            The running daemon thread (already started).
        """
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise ImportError(
                "sounddevice is required for VAD streaming. "
                'Install it with: pip install "voice-assistant[audio]"'
            ) from exc

        _stop = stop_event or threading.Event()

        def _run() -> None:
            log.debug("VAD listener started (threshold=%.2f)", self._threshold)
            n_samples = _CHUNK_BYTES // 2
            with sd.RawInputStream(
                samplerate=self._sample_rate,
                channels=1,
                dtype="int16",
                blocksize=n_samples,
            ) as stream:
                while not _stop.is_set():
                    data, _ = stream.read(n_samples)
                    if self.detect(bytes(data)):
                        log.debug("VAD: speech detected")
                        callback()
            log.debug("VAD listener stopped")

        t = threading.Thread(target=_run, daemon=True, name="va-vad")
        t.start()
        return t
