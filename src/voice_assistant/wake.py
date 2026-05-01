"""Always-on wake-word listener.

Runs on a background thread; samples the mic in 80 ms chunks; feeds them
into openWakeWord. When the detection score crosses the threshold, fires the
provided callback (which the GUI uses to trigger record_and_respond).

The openWakeWord Model is NOT imported or constructed at module load time — it
is imported lazily inside WakeWordListener.start() so that the rest of the
application starts even if the `wake` extra is not installed.
"""
from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

log = logging.getLogger(__name__)

# Microphone chunk size: 80 ms at 16 kHz → 1 280 samples.
_CHUNK_SAMPLES = 1280
_SAMPLE_RATE = 16000


class WakeWordError(Exception):
    """Raised when the wake-word subsystem cannot initialise."""


class WakeWordListener:
    """Background thread that listens for a wake word and fires a callback.

    Parameters
    ----------
    wake_word:
        One of the built-in openWakeWord model names, e.g. ``"hey_jarvis"``,
        ``"alexa"``, ``"hey_mycroft"``.
    sensitivity:
        Detection threshold in [0, 1].  Higher means fewer false positives but
        easier to miss real activations.  Default 0.5.
    on_wake:
        Zero-argument callable invoked (from the listener thread) each time
        the wake word is detected.
    """

    def __init__(
        self,
        *,
        wake_word: str = "hey_jarvis",
        sensitivity: float = 0.5,
        on_wake: Callable[[], None],
    ) -> None:
        self._wake_word = wake_word
        self._sensitivity = sensitivity
        self._on_wake = on_wake
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._model: Any = None  # lazily created in start()

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Initialise the model and start the background listener thread."""
        if self._thread is not None and self._thread.is_alive():
            log.warning("WakeWordListener.start() called while already running — ignored")
            return

        # Lazy import so the rest of the app works without the wake extra.
        try:
            from openwakeword.model import Model
        except ImportError as exc:
            raise WakeWordError(
                "openWakeWord is not installed. "
                'Install the `wake` extra: pip install "voice-assistant[wake]"'
            ) from exc

        try:
            import sounddevice as sd
        except ImportError as exc:
            raise WakeWordError(
                "sounddevice is not installed. "
                'Install the `audio` extra: pip install "voice-assistant[audio]"'
            ) from exc

        # Model files are downloaded on first use to ~/.cache/openwakeword/.
        # inference_framework="onnx" avoids the tflite dependency.
        self._model = Model(wakeword_models=[self._wake_word], inference_framework="onnx")
        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            args=(sd,),
            daemon=True,
            name=f"wake-word-{self._wake_word}",
        )
        self._thread.start()
        log.info("WakeWordListener started: wake_word=%r sensitivity=%s",
                 self._wake_word, self._sensitivity)

    def stop(self) -> None:
        """Signal the listener thread to stop and wait for it to exit."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        log.info("WakeWordListener stopped")

    # ------------------------------------------------------------------
    def _run(self, sd: Any) -> None:
        """Main loop running in the background thread."""
        log.debug("wake-word loop starting, chunk=%d samples", _CHUNK_SAMPLES)
        try:
            with sd.InputStream(
                samplerate=_SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=_CHUNK_SAMPLES,
            ) as stream:
                while not self._stop_event.is_set():
                    audio_chunk, _overflowed = stream.read(_CHUNK_SAMPLES)
                    # openwakeword expects a 1-D int16 NumPy array.
                    flat = audio_chunk[:, 0] if audio_chunk.ndim == 2 else audio_chunk
                    prediction = self._model.predict(flat)
                    score = prediction.get(self._wake_word, 0.0)
                    if score >= self._sensitivity:
                        log.info("wake word detected (score=%.3f)", score)
                        try:
                            self._on_wake()
                        except Exception:
                            log.exception("on_wake callback raised")
        except Exception:
            log.exception("WakeWordListener loop crashed")
