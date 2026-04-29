import numpy as np
from voice_assistant.stt import Transcriber, AudioBuffer


def test_transcriber_on_silence_returns_empty_or_short():
    sample_rate = 16000
    audio = np.zeros(sample_rate, dtype=np.float32)  # 1 sec silence
    buf = AudioBuffer(samples=audio, sample_rate=sample_rate)
    t = Transcriber(model_name="tiny")  # smallest model, downloads on first run
    out = t.transcribe(buf)
    assert isinstance(out, str)
    assert len(out) < 30  # silence -> empty or near-empty
