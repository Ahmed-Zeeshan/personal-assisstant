import wave
from pathlib import Path

import pytest

from voice_assistant.tts.piper_engine import PiperSpeaker


@pytest.fixture(scope="module")
def speaker() -> PiperSpeaker:
    """Reuse one PiperSpeaker across this file's tests to avoid re-loading the model."""
    return PiperSpeaker(voice="en_US-amy-medium")


def test_speaker_writes_valid_wav(speaker, tmp_path: Path):
    out = tmp_path / "out.wav"
    speaker.synthesise_to_file("hello world", out)
    assert out.exists() and out.stat().st_size > 1000
    with wave.open(str(out)) as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2  # 16-bit
        assert w.getnframes() > 8000  # ~0.36s at 22050 Hz; "hello world" ≈ 1s


def test_synthesise_empty_text_is_noop(speaker, tmp_path: Path):
    out = tmp_path / "empty.wav"
    speaker.synthesise_to_file("", out)
    # Should not raise, and should not have created a malformed wav.
    assert not out.exists() or out.stat().st_size == 0


def test_invalid_voice_name_raises_clear_error(tmp_path, monkeypatch):
    # Point the cache at a temp dir so we attempt a fresh download
    monkeypatch.setattr("voice_assistant.tts.piper_engine._CACHE_DIR", tmp_path)
    with pytest.raises(ValueError, match="Invalid piper voice"):
        PiperSpeaker(voice="completely_bogus_voice_name_xyz")
