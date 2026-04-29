from __future__ import annotations
import logging
import queue
import threading
import time
import numpy as np
import sounddevice as sd
from pynput import keyboard
from voice_assistant.stt import AudioBuffer

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000
BLOCK_SECONDS = 0.1


def detect_silence(samples: np.ndarray, threshold: float = 0.01) -> bool:
    rms = float(np.sqrt(np.mean(samples ** 2)))
    return rms < threshold


def record_until_silence(
    silence_seconds: float = 1.5,
    max_seconds: float = 15.0,
) -> AudioBuffer:
    """Record from default mic until `silence_seconds` of quiet (or timeout)."""
    q: queue.Queue[np.ndarray] = queue.Queue()

    def cb(indata, frames, time_info, status):
        if status:
            log.warning("audio status: %s", status)
        q.put(indata.copy().flatten())

    chunks: list[np.ndarray] = []
    silence_blocks_needed = int(silence_seconds / BLOCK_SECONDS)
    silence_run = 0
    t_start = time.monotonic()

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=int(SAMPLE_RATE * BLOCK_SECONDS),
        callback=cb,
    ):
        while time.monotonic() - t_start < max_seconds:
            try:
                block = q.get(timeout=0.5)
            except queue.Empty:
                continue
            chunks.append(block)
            if detect_silence(block):
                silence_run += 1
                if silence_run >= silence_blocks_needed and len(chunks) > silence_blocks_needed:
                    break
            else:
                silence_run = 0

    samples = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
    return AudioBuffer(samples=samples, sample_rate=SAMPLE_RATE)


class HotkeyListener:
    """Blocks until the configured hotkey is pressed once."""

    def __init__(self, hotkey: str) -> None:
        self.hotkey = hotkey
        self._event = threading.Event()
        self._listener: keyboard.GlobalHotKeys | None = None

    def _trigger(self) -> None:
        self._event.set()

    def wait_for_press(self) -> None:
        self._event.clear()
        with keyboard.GlobalHotKeys({self._normalised(): self._trigger}):
            self._event.wait()

    def _normalised(self) -> str:
        # pynput expects e.g. "<ctrl>+<shift>+<space>"; we accept "ctrl+shift+space"
        parts = [p.strip().lower() for p in self.hotkey.split("+")]
        out = []
        specials = {"ctrl", "shift", "alt", "cmd", "space", "enter", "tab", "esc"}
        for p in parts:
            out.append(f"<{p}>" if p in specials else p)
        return "+".join(out)
