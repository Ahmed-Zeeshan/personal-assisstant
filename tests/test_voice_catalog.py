from voice_assistant.voice_catalog import VOICES, voices_for, find_voice


def test_catalog_has_english_piper():
    p = find_voice("piper:en_US-amy-medium")
    assert p is not None
    assert p.engine == "piper"
    assert p.language == "en"


def test_catalog_has_openai_voices():
    o = find_voice("openai:nova")
    assert o is not None
    assert o.engine == "openai"
    assert "Nova" in o.label


def test_catalog_has_urdu_via_openai():
    urdu_voices = voices_for(language="ur")
    assert any(v.engine == "openai" for v in urdu_voices), \
        "OpenAI TTS supports Urdu — at least one Urdu voice expected"


def test_catalog_has_hindi():
    hi = voices_for(language="hi")
    assert len(hi) >= 1


def test_european_languages_covered():
    for lang in ["cs", "sk", "de", "fr", "es", "it", "pl", "nl", "ro"]:
        vs = voices_for(language=lang)
        assert len(vs) >= 1, f"no voices found for language {lang}"
