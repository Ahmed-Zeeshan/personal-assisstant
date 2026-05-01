import pytest

from voice_assistant.tts import make_speaker


def test_factory_rejects_unknown_voice():
    with pytest.raises(ValueError):
        make_speaker(voice_id="bogus:invalid")


def test_factory_returns_piper_for_known_piper_voice(monkeypatch):
    # PiperSpeaker import happens lazily; mock it before we hit the actual class.
    class FakePiper:
        def __init__(self, voice: str) -> None:
            self.voice = voice

        def speak(self, text: str) -> None:
            pass

    import voice_assistant.tts.piper_engine as pe

    monkeypatch.setattr(pe, "PiperSpeaker", FakePiper)
    sp = make_speaker(voice_id="piper:en_US-amy-medium")
    assert isinstance(sp, FakePiper)
    assert sp.voice == "en_US-amy-medium"


def test_factory_returns_openai_for_openai_voice(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    sp = make_speaker(voice_id="openai:nova")
    from voice_assistant.tts.openai_engine import OpenAISpeaker

    assert isinstance(sp, OpenAISpeaker)


def test_factory_legacy_bare_voice_is_treated_as_piper(monkeypatch):
    class FakePiper:
        def __init__(self, voice: str) -> None:
            self.voice = voice

        def speak(self, text: str) -> None:
            pass

    import voice_assistant.tts.piper_engine as pe

    monkeypatch.setattr(pe, "PiperSpeaker", FakePiper)
    sp = make_speaker(voice_id="en_US-amy-medium")
    assert isinstance(sp, FakePiper)
