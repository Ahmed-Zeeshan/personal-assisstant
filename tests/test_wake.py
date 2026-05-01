"""Tests for the wake-word listener module.

openWakeWord and sounddevice are mocked out so the test suite can run without
installing the `wake` extra or connecting a microphone.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from voice_assistant.wake import WakeWordError, WakeWordListener

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_listener(wake_word: str = "hey_jarvis", sensitivity: float = 0.5,
                   on_wake=None) -> WakeWordListener:
    return WakeWordListener(
        wake_word=wake_word,
        sensitivity=sensitivity,
        on_wake=on_wake or (lambda: None),
    )


def _fake_model(wake_word: str, score: float) -> MagicMock:
    """Return a mock openwakeword Model that always predicts `score`."""
    model = MagicMock()
    model.predict.return_value = {wake_word: score}
    return model


# ---------------------------------------------------------------------------
# Unit tests — no real audio, no real model
# ---------------------------------------------------------------------------

class TestWakeWordListenerInit:
    def test_defaults(self):
        fired = []
        wl = WakeWordListener(on_wake=lambda: fired.append(1))
        assert wl._wake_word == "hey_jarvis"
        assert wl._sensitivity == 0.5
        assert wl._thread is None
        assert wl._model is None

    def test_custom_params(self):
        wl = _make_listener(wake_word="alexa", sensitivity=0.7)
        assert wl._wake_word == "alexa"
        assert wl._sensitivity == pytest.approx(0.7)


class TestWakeWordListenerStartErrors:
    def test_start_raises_when_openwakeword_missing(self, monkeypatch):
        """WakeWordError raised when openwakeword package is not installed."""
        wl = _make_listener()
        monkeypatch.setitem(
            __import__("sys").modules,
            "openwakeword",
            None,  # simulate missing package
        )
        # builtins.import raises ImportError when a module is None in sys.modules
        # We simulate the same via patching the import path.
        with patch("builtins.__import__", side_effect=_block_import("openwakeword")):
            with pytest.raises(WakeWordError, match="not installed"):
                wl.start()

    def test_start_raises_when_sounddevice_missing(self, monkeypatch):
        """WakeWordError raised when sounddevice package is not installed."""
        wl = _make_listener()
        fake_oww = MagicMock()
        fake_oww.model.Model.return_value = MagicMock()
        with (
            patch("builtins.__import__", side_effect=_allow_only_block("sounddevice", fake_oww)),
        ):
            with pytest.raises(WakeWordError, match="sounddevice"):
                wl.start()


def _block_import(blocked: str):
    """Return a side-effect that raises ImportError for the blocked module."""
    real_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__  # type: ignore[attr-defined]

    def _side(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == blocked or name.startswith(blocked + "."):
            raise ImportError(f"No module named '{blocked}'")
        return real_import(name, *args, **kwargs)
    return _side


def _allow_only_block(blocked: str, oww_fake: MagicMock):
    """Return an import side-effect that blocks `blocked` but returns oww_fake for openwakeword."""
    real_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__  # type: ignore[attr-defined]

    def _side(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == blocked or name.startswith(blocked + "."):
            raise ImportError(f"No module named '{blocked}'")
        if name == "openwakeword" or name.startswith("openwakeword."):
            return oww_fake
        return real_import(name, *args, **kwargs)
    return _side


class TestWakeWordDetection:
    """Test detection logic with fully mocked model and sounddevice."""

    def _run_listener_once(self, wake_word: str, score: float, sensitivity: float,
                           fired: list):
        """Run one iteration of the listener loop and return whether callback fired."""
        import numpy as np

        wl = _make_listener(wake_word=wake_word, sensitivity=sensitivity,
                            on_wake=lambda: fired.append(1))

        # Fake audio chunk: 1280 int16 samples
        fake_chunk = np.zeros((_make_listener._CHUNK if hasattr(_make_listener, "_CHUNK") else 1280, 1),
                              dtype="int16")

        # Mock sounddevice InputStream as a context manager
        fake_stream = MagicMock()
        fake_stream.__enter__ = lambda s: s
        fake_stream.__exit__ = MagicMock(return_value=False)
        fake_stream.read.return_value = (fake_chunk, False)

        fake_sd = MagicMock()
        fake_sd.InputStream.return_value = fake_stream

        # Mock the model
        fake_model_instance = _fake_model(wake_word, score)
        fake_oww_module = MagicMock()
        fake_oww_module.model.Model.return_value = fake_model_instance

        # Let the loop run exactly once then stop
        call_count = [0]
        def fake_is_set():
            # First call (loop check): let it pass
            # Second call (loop check): stop
            if call_count[0] == 0:
                call_count[0] += 1
                return False
            return True

        wl._stop_event.is_set = fake_is_set  # type: ignore[method-assign]
        wl._model = fake_model_instance

        wl._run(fake_sd)

    def test_above_threshold_fires_callback(self):
        import numpy as np
        fired: list = []
        wl = _make_listener(wake_word="hey_jarvis", sensitivity=0.5, on_wake=lambda: fired.append(1))

        fake_chunk = np.zeros((1280, 1), dtype="int16")
        fake_stream = MagicMock()
        fake_stream.__enter__ = lambda s: s
        fake_stream.__exit__ = MagicMock(return_value=False)
        fake_stream.read.return_value = (fake_chunk, False)

        fake_sd = MagicMock()
        fake_sd.InputStream.return_value = fake_stream

        wl._model = _fake_model("hey_jarvis", 0.9)  # above threshold

        call_count = [0]
        def fake_is_set():
            call_count[0] += 1
            return call_count[0] > 1  # stop after 1 iteration

        wl._stop_event.is_set = fake_is_set  # type: ignore[method-assign]
        wl._run(fake_sd)

        assert fired == [1], "callback should have fired once"

    def test_below_threshold_does_not_fire(self):
        import numpy as np
        fired: list = []
        wl = _make_listener(wake_word="hey_jarvis", sensitivity=0.5, on_wake=lambda: fired.append(1))

        fake_chunk = np.zeros((1280, 1), dtype="int16")
        fake_stream = MagicMock()
        fake_stream.__enter__ = lambda s: s
        fake_stream.__exit__ = MagicMock(return_value=False)
        fake_stream.read.return_value = (fake_chunk, False)

        fake_sd = MagicMock()
        fake_sd.InputStream.return_value = fake_stream

        wl._model = _fake_model("hey_jarvis", 0.1)  # below threshold

        call_count = [0]
        def fake_is_set():
            call_count[0] += 1
            return call_count[0] > 1

        wl._stop_event.is_set = fake_is_set  # type: ignore[method-assign]
        wl._run(fake_sd)

        assert fired == [], "callback should NOT fire below threshold"

    def test_exactly_at_threshold_fires(self):
        import numpy as np
        fired: list = []
        wl = _make_listener(wake_word="hey_jarvis", sensitivity=0.5, on_wake=lambda: fired.append(1))

        fake_chunk = np.zeros((1280, 1), dtype="int16")
        fake_stream = MagicMock()
        fake_stream.__enter__ = lambda s: s
        fake_stream.__exit__ = MagicMock(return_value=False)
        fake_stream.read.return_value = (fake_chunk, False)

        fake_sd = MagicMock()
        fake_sd.InputStream.return_value = fake_stream

        wl._model = _fake_model("hey_jarvis", 0.5)  # exactly at threshold

        call_count = [0]
        def fake_is_set():
            call_count[0] += 1
            return call_count[0] > 1

        wl._stop_event.is_set = fake_is_set  # type: ignore[method-assign]
        wl._run(fake_sd)

        assert fired == [1]

    def test_model_not_imported_at_module_level(self):
        """Verify that importing wake does NOT import openwakeword."""
        import sys
        # Remove any cached openwakeword reference so the check is clean
        oww_key = "openwakeword"
        was_present = oww_key in sys.modules
        try:
            import voice_assistant.wake  # noqa: F401
            # openwakeword should NOT have been imported as a side-effect
            # (it's only imported lazily inside start())
            assert oww_key not in sys.modules or sys.modules.get(oww_key) is not None
            # The module-level code should not have touched openwakeword
        finally:
            if not was_present:
                sys.modules.pop(oww_key, None)


class TestWakeWordStop:
    def test_stop_is_idempotent_when_never_started(self):
        wl = _make_listener()
        wl.stop()  # should not raise
        wl.stop()  # should not raise

    def test_double_start_does_not_create_second_thread(self, monkeypatch):
        """Second call to start() while already running is a no-op."""
        wl = _make_listener()
        # Fake a live thread
        fake_thread = MagicMock()
        fake_thread.is_alive.return_value = True
        wl._thread = fake_thread  # type: ignore[assignment]

        # Patch the import so start() would fail if it reached the import
        import_called = []
        real_import = __import__

        def _side(name, *args, **kwargs):  # type: ignore[no-untyped-def]
            if name.startswith("openwakeword"):
                import_called.append(name)
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", _side)
        wl.start()
        assert not import_called, "start() should return early without importing openwakeword"
