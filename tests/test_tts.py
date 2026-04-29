from pathlib import Path
from voice_assistant.tts import Speaker


def test_speaker_writes_wav(tmp_path: Path):
    out = tmp_path / "out.wav"
    s = Speaker(voice="en_US-amy-medium")
    s.synthesise_to_file("hello world", out)
    assert out.exists() and out.stat().st_size > 1000
