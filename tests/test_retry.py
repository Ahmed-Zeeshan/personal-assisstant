import pytest

from voice_assistant.retry import with_llm_retry


def test_retries_on_transient_error_then_succeeds(monkeypatch):
    calls = {"n": 0}

    @with_llm_retry(max_attempts=3, base_delay=0.0)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("transient")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3


def test_gives_up_after_max_attempts():
    @with_llm_retry(max_attempts=2, base_delay=0.0)
    def always_broken():
        raise ConnectionError("nope")

    with pytest.raises(ConnectionError):
        always_broken()


def test_does_not_retry_on_value_error():
    """ValueError is a programming bug, not a transient — don't retry."""
    calls = {"n": 0}

    @with_llm_retry(max_attempts=3, base_delay=0.0)
    def bad():
        calls["n"] += 1
        raise ValueError("bug")

    with pytest.raises(ValueError):
        bad()
    assert calls["n"] == 1
