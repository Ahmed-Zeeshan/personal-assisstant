import numpy as np
import pytest

from voice_assistant.stt import AudioBuffer, Transcriber


@pytest.fixture(scope="module")
def transcriber() -> Transcriber:
    """Reuse the same model across this file's tests to avoid re-download."""
    return Transcriber(model_name="tiny")


def test_transcribe_silence_returns_string(transcriber):
    sample_rate = 16000
    audio = np.zeros(sample_rate, dtype=np.float32)
    out = transcriber.transcribe(AudioBuffer(samples=audio, sample_rate=sample_rate))
    assert isinstance(out, str)
    # Whisper occasionally hallucinates on silence; we only check it returns a string.


def test_transcribe_empty_buffer_returns_empty_string(transcriber):
    out = transcriber.transcribe(
        AudioBuffer(samples=np.zeros(0, dtype=np.float32), sample_rate=16000)
    )
    assert out == ""


def test_transcribe_rejects_wrong_sample_rate(transcriber):
    audio = np.zeros(8000, dtype=np.float32)
    with pytest.raises(ValueError, match="16kHz"):
        transcriber.transcribe(AudioBuffer(samples=audio, sample_rate=8000))


def test_transcribe_rejects_stereo(transcriber):
    audio = np.zeros((16000, 2), dtype=np.float32)
    with pytest.raises(ValueError, match="mono"):
        transcriber.transcribe(AudioBuffer(samples=audio, sample_rate=16000))


def test_transcribe_rejects_wrong_dtype(transcriber):
    audio = np.zeros(16000, dtype=np.int16)
    with pytest.raises(ValueError, match="float32"):
        transcriber.transcribe(AudioBuffer(samples=audio, sample_rate=16000))
