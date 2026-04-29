import numpy as np
from voice_assistant.audio_input import detect_silence


def test_detect_silence_on_zeros():
    buf = np.zeros(16000, dtype=np.float32)  # 1s silence
    assert detect_silence(buf, threshold=0.01)


def test_detect_silence_on_loud_signal():
    buf = (np.random.rand(16000).astype(np.float32) * 0.5)
    assert not detect_silence(buf, threshold=0.01)
