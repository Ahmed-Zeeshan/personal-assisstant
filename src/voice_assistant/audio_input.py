from __future__ import annotations

import logging
import queue
import threading
import time
from collections.abc import Callable

import numpy as np
import sounddevice as sd
from pynput import keyboard

from voice_assistant.audio_types import AudioBuffer

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000
BLOCK_SECONDS = 0.1


def detect_silence(samples: np.ndarray, threshold: float = 0.01) -> bool:
    if samples.size == 0:
        return True
    rms = float(np.sqrt(np.mean(samples**2)))
    return rms < threshold


def record_until_silence(
    silence_seconds: float = 1.5,
    max_seconds: float = 15.0,
    *,
    level_callback: Callable[[float], None] | None = None,
) -> AudioBuffer:
    """Record from default mic until `silence_seconds` of quiet (after first
    speech) or until `max_seconds` elapses.

    Args:
        silence_seconds: Seconds of silence before stopping.
        max_seconds: Hard cutoff in seconds.
        level_callback: Optional keyword-only callback invoked per audio chunk
            with the current RMS level normalised to 0..1.
    """
    q: queue.Queue[np.ndarray] = queue.Queue()

    def cb(indata: np.ndarray, frames: int, time_info: object, status: object) -> None:
        if status:
            log.warning("audio status: %s", status)
        q.put(indata.copy().flatten())

    chunks: list[np.ndarray] = []
    silence_blocks_needed = int(silence_seconds / BLOCK_SECONDS)
    silence_run = 0
    saw_speech = False
    t_start = time.monotonic()

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=int(SAMPLE_RATE * BLOCK_SECONDS),
        callback=cb,
    ):
        while True:
            remaining = t_start + max_seconds - time.monotonic()
            if remaining <= 0:
                break
            try:
                block = q.get(timeout=min(0.5, remaining))
            except queue.Empty:
                continue
            chunks.append(block)
            if level_callback is not None:
                rms = float(np.sqrt(np.mean(block.astype("float32") ** 2)))
                level_callback(min(1.0, rms))
            if detect_silence(block):
                silence_run += 1
                if saw_speech and silence_run >= silence_blocks_needed:
                    break
            else:
                silence_run = 0
                saw_speech = True

    samples = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
    return AudioBuffer(samples=samples, sample_rate=SAMPLE_RATE)


class HotkeyListener:
    """Blocks until the configured hotkey is pressed once."""

    def __init__(self, hotkey: str) -> None:
        self.hotkey = hotkey
        self._event = threading.Event()

    def _trigger(self) -> None:
        self._event.set()

    def wait_for_press(self) -> None:
        self._event.clear()
        with keyboard.GlobalHotKeys({self._normalised(): self._trigger}):
            self._event.wait()

    def _normalised(self) -> str:
        """Translate friendly hotkey strings to pynput's `<token>+<token>` form.

        Any token longer than one character is wrapped in angle brackets.
        Single-character tokens (literal letters/digits) stay bare.
        """
        parts = [p.strip().lower() for p in self.hotkey.split("+")]
        return "+".join(f"<{p}>" if len(p) != 1 else p for p in parts)
