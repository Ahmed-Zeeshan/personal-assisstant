import numpy as np
import pytest

from voice_assistant.audio_input import HotkeyListener, detect_silence

# ---------- detect_silence ----------

def test_detect_silence_on_zeros():
    buf = np.zeros(16000, dtype=np.float32)
    assert detect_silence(buf, threshold=0.01)


def test_detect_silence_on_loud_signal():
    buf = (np.random.rand(16000).astype(np.float32) * 0.5)
    assert not detect_silence(buf, threshold=0.01)


def test_detect_silence_on_empty_array_is_silent():
    buf = np.zeros(0, dtype=np.float32)
    assert detect_silence(buf)


# ---------- HotkeyListener._normalised ----------

@pytest.mark.parametrize("raw,expected", [
    ("ctrl+shift+space", "<ctrl>+<shift>+<space>"),
    ("Ctrl+Shift+Space", "<ctrl>+<shift>+<space>"),
    ("ctrl + shift + space", "<ctrl>+<shift>+<space>"),
    ("ctrl+c", "<ctrl>+c"),
    ("space", "<space>"),
    ("ctrl+f1", "<ctrl>+<f1>"),
    ("ctrl+backspace", "<ctrl>+<backspace>"),
    ("alt+a", "<alt>+a"),
])
def test_hotkey_normalisation(raw, expected):
    assert HotkeyListener(raw)._normalised() == expected
