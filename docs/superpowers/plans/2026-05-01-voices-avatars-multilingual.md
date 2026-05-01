# Voices + Avatars + Multilingual + Speed — combined plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use `- [ ]` checkbox syntax.

**Goal:** Eight coordinated changes that lift the assistant from "talks in Amy's English voice via Piper" to "speaks any of 30+ languages including Urdu and Hindi in 6+ premium voices, with an animated avatar centerpiece that replaces the orb, all responding faster":

1. **OpenAI TTS engine** — premium multilingual voices (alloy, echo, fable, onyx, nova, shimmer + gpt-4o-mini-tts variants). Falls back to Piper for offline English.
2. **Voice catalog** — single registry of voices with `{id, label, language, gender, engine}`. ~30 entries.
3. **STT language config** — `auto` (default) | specific code (`en`, `ur`, `hi`, `cs`, `sk`, …). faster-whisper handles all of them.
4. **System prompt language rule** — "respond in the same language the user used; if they switch, switch with them."
5. **Animated avatar** — DiceBear-generated SVG portrait that pulses breathing while idle, halos on listening, bobs on speaking, shows "thinking" dots. Replaces the orb as the centerpiece. Three picks: Aria (female), Liam (male), Sage (neutral).
6. **Streaming TTS** — split LLM stream on sentence boundaries; synthesise each sentence and queue for playback while later sentences are still being generated. Cuts time-to-first-audio from "full reply" (~3-8s) to "first sentence" (~600ms).
7. **Default to faster models per provider** — Anthropic `claude-haiku-4-5`, OpenAI `gpt-5.4-mini`, Gemini `gemini-3.1-flash`. User can override via Settings dropdown (full models still listed).
8. **Settings UX** — Avatar picker (grid of 3) + Voice picker (grouped by language, with "▶ Test" button) + Language picker (auto / pin to specific language).

**Architecture:**
- `src/voice_assistant/tts/__init__.py` exports `Speaker` ABC and `make_speaker(cfg, user_voice)` factory. Two implementations: `PiperSpeaker`, `OpenAISpeaker`.
- `tts/streaming.py` exposes `SentenceQueueSpeaker` that wraps any `Speaker` and a sentence chunker. The orchestrator's stream feeds sentences in; `SentenceQueueSpeaker` synthesises them in a background thread and plays via `sounddevice`.
- `voice_catalog.py` is the single source of truth for the voices list. The bridge sends it to JS; the Settings drawer renders it.
- The Orb component is **kept** (still useful) but a new `Avatar` component is now the centerpiece. The orb shrinks into a small status-light pill in the header. User can swap them via Settings (default: Avatar).
- DiceBear is used at build time only — three SVGs are downloaded and committed under `web/public/avatars/{aria,liam,sage}.svg` so the GUI works offline. License is permissive (Avataaars: CC0; bottts: MIT; etc).

**Tech Stack:** OpenAI TTS API · sounddevice (already there) · faster-whisper (already there, supports 99+ languages) · pure SVG/CSS for avatars · LiteLLM for embeddings already pulled in.

---

## File Structure

**Created:**
- `src/voice_assistant/voice_catalog.py`
- `src/voice_assistant/tts/__init__.py`
- `src/voice_assistant/tts/base.py` (Speaker ABC)
- `src/voice_assistant/tts/piper_engine.py` (existing logic moved here)
- `src/voice_assistant/tts/openai_engine.py`
- `src/voice_assistant/tts/streaming.py`
- `tests/test_voice_catalog.py`
- `tests/test_tts_factory.py`
- `tests/test_tts_streaming.py`
- `web/public/avatars/aria.svg`
- `web/public/avatars/liam.svg`
- `web/public/avatars/sage.svg`
- `web/src/components/Avatar.ts`

**Modified:**
- `src/voice_assistant/tts.py` — DELETE (replaced by package).
- `src/voice_assistant/config.py` — TTSConfig accepts `engine` literal, `voice` free-form id; STTConfig accepts `language: "auto" | <code>`.
- `src/voice_assistant/setup_wizard.py` — render voice + STT language; wizard prompts for voice.
- `src/voice_assistant/brain.py` — system prompt adds "respond in user's language".
- `src/voice_assistant/cli.py` — `make_speaker(cfg, user_voice)` factory call; voice mode uses streaming speaker.
- `src/voice_assistant/desktop/bridge.py` — `get_config` returns `available_voices`, `available_avatars`; `save_config` accepts `voice`, `avatar`, `stt_language`.
- `web/src/types.ts` — extends AppConfig.
- `web/src/components/Settings.ts` — voice picker + avatar picker + language picker.
- `web/src/main.ts` — Avatar replaces Orb in the layout (Orb retained as small header indicator).
- `src/voice_assistant/setup_wizard.py` DEFAULT_MODELS now point to faster tier.

---

## Task 1: Voice catalog + config schema

**Files:**
- Create: `src/voice_assistant/voice_catalog.py`
- Modify: `src/voice_assistant/config.py` — extend TTSConfig + STTConfig

- [ ] **Step 1: Failing test**

```python
# tests/test_voice_catalog.py
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
```

- [ ] **Step 2: Implement `voice_catalog.py`**

```python
"""Single source of truth for available TTS voices.

Each voice has:
  id        — engine-prefixed unique key, e.g. "openai:nova" or "piper:en_US-amy-medium"
  label     — human-readable display name
  language  — ISO 639-1 (e.g. "en", "ur", "hi")
  gender    — "female" | "male" | "neutral"
  engine    — "piper" | "openai"
  notes     — optional, shown as small text in the UI
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Voice:
    id: str
    label: str
    language: str
    gender: Literal["female", "male", "neutral"]
    engine: Literal["piper", "openai"]
    notes: str = ""


# OpenAI TTS — gpt-4o-mini-tts model supports 50+ languages with the same voice.
# Listed languages are the primary UI categorisations; the voice itself works for
# all supported languages of the underlying model.
_OPENAI_VOICES = [
    ("alloy",   "Alloy — neutral, calm",       "neutral"),
    ("echo",    "Echo — warm, male",           "male"),
    ("fable",   "Fable — British, male",       "male"),
    ("onyx",    "Onyx — deep, male",           "male"),
    ("nova",    "Nova — friendly, female",     "female"),
    ("shimmer", "Shimmer — bright, female",    "female"),
    ("coral",   "Coral — gentle, female",      "female"),
    ("sage",    "Sage — measured, neutral",    "neutral"),
    ("ash",     "Ash — confident, male",       "male"),
    ("ballad",  "Ballad — expressive, female", "female"),
]
_OPENAI_LANGUAGES = [
    ("en", "English"), ("ur", "Urdu"), ("hi", "Hindi"),
    ("ar", "Arabic"), ("zh", "Chinese"), ("ja", "Japanese"), ("ko", "Korean"),
    ("de", "German"), ("fr", "French"), ("es", "Spanish"), ("it", "Italian"),
    ("pt", "Portuguese"), ("ru", "Russian"), ("nl", "Dutch"), ("pl", "Polish"),
    ("cs", "Czech"), ("sk", "Slovak"), ("hu", "Hungarian"), ("ro", "Romanian"),
    ("tr", "Turkish"), ("uk", "Ukrainian"), ("el", "Greek"), ("sv", "Swedish"),
    ("da", "Danish"), ("no", "Norwegian"), ("fi", "Finnish"), ("bg", "Bulgarian"),
    ("hr", "Croatian"), ("sr", "Serbian"), ("vi", "Vietnamese"), ("id", "Indonesian"),
    ("th", "Thai"), ("he", "Hebrew"), ("fa", "Persian"),
]

_PIPER_VOICES = [
    # English (offline, fast — default)
    ("en_US-amy-medium",       "Amy — US English (default)",   "en", "female"),
    ("en_US-ryan-medium",      "Ryan — US English",            "en", "male"),
    ("en_US-libritts-high",    "LibriTTS HQ — US English",     "en", "neutral"),
    ("en_GB-alan-medium",      "Alan — UK English",            "en", "male"),
    ("en_GB-jenny_dioco-medium","Jenny — UK English",          "en", "female"),
]

VOICES: list[Voice] = []

# OpenAI: each voice × each language is one VOICES entry. The id stays voice-only;
# `language` is metadata used for filtering. The OpenAI TTS engine ignores language
# (the model auto-detects); we only use it to group in the UI.
for lang, lang_label in _OPENAI_LANGUAGES:
    for vid, vlabel, vgender in _OPENAI_VOICES:
        VOICES.append(Voice(
            id=f"openai:{vid}",
            label=f"{vlabel} ({lang_label})" if lang != "en" else vlabel,
            language=lang,
            gender=vgender,  # type: ignore[arg-type]
            engine="openai",
            notes="online · OpenAI · multilingual",
        ))

for vid, vlabel, vlang, vgender in _PIPER_VOICES:
    VOICES.append(Voice(
        id=f"piper:{vid}",
        label=vlabel,
        language=vlang,
        gender=vgender,  # type: ignore[arg-type]
        engine="piper",
        notes="offline · Piper",
    ))


def voices_for(*, language: str | None = None, engine: str | None = None) -> list[Voice]:
    out = VOICES
    if language is not None:
        out = [v for v in out if v.language == language]
    if engine is not None:
        out = [v for v in out if v.engine == engine]
    return out


def find_voice(voice_id: str) -> Voice | None:
    for v in VOICES:
        if v.id == voice_id:
            return v
    return None


# A short list of STT languages exposed in the UI (faster-whisper handles 99 — these
# are the user-friendly highlights).
STT_LANGUAGES: list[tuple[str, str]] = [
    ("auto", "Auto-detect"),
    ("en", "English"),
    ("ur", "Urdu"),
    ("hi", "Hindi"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("it", "Italian"),
    ("pt", "Portuguese"),
    ("ru", "Russian"),
    ("zh", "Chinese"),
    ("ja", "Japanese"),
    ("ar", "Arabic"),
    ("nl", "Dutch"),
    ("pl", "Polish"),
    ("cs", "Czech"),
    ("sk", "Slovak"),
    ("hu", "Hungarian"),
    ("ro", "Romanian"),
    ("tr", "Turkish"),
    ("uk", "Ukrainian"),
    ("el", "Greek"),
    ("sv", "Swedish"),
    ("fi", "Finnish"),
    ("no", "Norwegian"),
]
```

- [ ] **Step 3: Modify `config.py`**

In `TTSConfig`:

```python
class TTSConfig(BaseModel):
    engine: Literal["piper", "openai"] = "piper"
    voice: str = "piper:en_US-amy-medium"   # full id from the catalog

    @field_validator("voice")
    @classmethod
    def _check_voice_id(cls, v: str) -> str:
        # Allow either bare piper voice (legacy: "en_US-amy-medium") or prefixed.
        if ":" not in v:
            return f"piper:{v}"
        return v
```

In `STTConfig`:

```python
class STTConfig(BaseModel):
    engine: Literal["faster-whisper"] = "faster-whisper"
    model: str = "small"
    language: str = "auto"   # "auto" or ISO 639-1 code
```

(Backward-compatible: existing configs with `language: en` still validate.)

- [ ] **Step 4: Tests pass**

```bash
~/.local/share/voice-assistant/.venv/bin/pytest tests/test_voice_catalog.py tests/test_config.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/voice_assistant/voice_catalog.py src/voice_assistant/config.py tests/test_voice_catalog.py
git commit -m "feat(tts): voice catalog (Piper + OpenAI, 30+ langs incl. Urdu/Hindi)"
```

---

## Task 2: TTS engines — Piper + OpenAI + factory

**Files:**
- Create: `src/voice_assistant/tts/__init__.py`
- Create: `src/voice_assistant/tts/base.py`
- Create: `src/voice_assistant/tts/piper_engine.py`
- Create: `src/voice_assistant/tts/openai_engine.py`
- Delete: `src/voice_assistant/tts.py` (move logic to `tts/piper_engine.py`)
- Create: `tests/test_tts_factory.py`

- [ ] **Step 1: Create `tts/base.py`**

```python
"""Speaker abstract base class. Each engine implements `speak(text)`."""
from __future__ import annotations
from abc import ABC, abstractmethod


class Speaker(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        """Synthesise and play `text`. Blocks until playback finishes."""
        raise NotImplementedError
```

- [ ] **Step 2: Move existing tts.py into `tts/piper_engine.py`**

Read the existing `src/voice_assistant/tts.py`. Wrap its class as `PiperSpeaker(Speaker)` (subclass of base). Constructor takes a Piper voice id (without the `piper:` prefix).

- [ ] **Step 3: Create `tts/openai_engine.py`**

```python
"""OpenAI TTS engine. Uses gpt-4o-mini-tts for premium multilingual voices.

Streams audio bytes from the OpenAI API and plays via sounddevice.
"""
from __future__ import annotations
import io
import logging
import os
from typing import Any

from voice_assistant.tts.base import Speaker

log = logging.getLogger(__name__)


class OpenAISpeaker(Speaker):
    """OpenAI TTS. Voice id is bare (e.g. 'nova'), not prefixed."""

    def __init__(self, voice: str, model: str = "gpt-4o-mini-tts") -> None:
        self._voice = voice
        self._model = model
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY not set; OpenAI TTS requires an API key. "
                "Set it via the wizard or settings drawer."
            )

    def speak(self, text: str) -> None:
        if not text.strip():
            return
        try:
            from openai import OpenAI  # type: ignore
            import sounddevice as sd  # type: ignore
            import soundfile as sf    # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI TTS dependencies missing. Install with: pip install openai soundfile"
            ) from exc

        client = OpenAI()
        # response_format=wav so soundfile/sounddevice can play directly.
        with client.audio.speech.with_streaming_response.create(
            model=self._model,
            voice=self._voice,
            input=text,
            response_format="wav",
        ) as response:
            buf = io.BytesIO()
            for chunk in response.iter_bytes():
                buf.write(chunk)
            buf.seek(0)
            data, samplerate = sf.read(buf, dtype="float32")
            sd.play(data, samplerate)
            sd.wait()
```

- [ ] **Step 4: Create `tts/__init__.py` factory**

```python
"""TTS factory: pick engine based on voice id."""
from __future__ import annotations
from voice_assistant.tts.base import Speaker
from voice_assistant.voice_catalog import find_voice


def make_speaker(*, voice_id: str) -> Speaker:
    """Construct the appropriate Speaker for the given voice id.

    voice_id has the form 'engine:name' — e.g. 'piper:en_US-amy-medium', 'openai:nova'.
    """
    if ":" not in voice_id:
        # Legacy: bare piper voice
        voice_id = f"piper:{voice_id}"

    voice = find_voice(voice_id)
    if voice is None:
        raise ValueError(f"unknown voice id: {voice_id!r}")

    engine, name = voice_id.split(":", 1)
    if engine == "piper":
        from voice_assistant.tts.piper_engine import PiperSpeaker
        return PiperSpeaker(voice=name)
    if engine == "openai":
        from voice_assistant.tts.openai_engine import OpenAISpeaker
        return OpenAISpeaker(voice=name)
    raise ValueError(f"unknown TTS engine: {engine!r}")


__all__ = ["Speaker", "make_speaker"]
```

- [ ] **Step 5: Tests**

```python
# tests/test_tts_factory.py
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
        def speak(self, text: str) -> None: pass

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
        def __init__(self, voice: str) -> None: self.voice = voice
        def speak(self, text: str) -> None: pass

    import voice_assistant.tts.piper_engine as pe
    monkeypatch.setattr(pe, "PiperSpeaker", FakePiper)
    sp = make_speaker(voice_id="en_US-amy-medium")
    assert isinstance(sp, FakePiper)
```

- [ ] **Step 6: Update all `from voice_assistant.tts import Speaker` callers**

`grep -r "voice_assistant.tts" --include="*.py"` and verify they still import correctly after the package conversion.

- [ ] **Step 7: Tests**

```bash
~/.local/share/voice-assistant/.venv/bin/pytest tests/test_tts_factory.py tests/test_tts.py -v
```

(`test_tts.py` may need fixes since it tested the old PiperSpeaker; update imports to point at `tts.piper_engine.PiperSpeaker`.)

- [ ] **Step 8: Commit**

```bash
git add src/voice_assistant/tts/ tests/test_tts_factory.py tests/test_tts.py
git rm src/voice_assistant/tts.py
git commit -m "feat(tts): pluggable engine — Piper + OpenAI multilingual"
```

---

## Task 3: Streaming TTS (sentence-by-sentence)

**Files:**
- Create: `src/voice_assistant/tts/streaming.py`
- Create: `tests/test_tts_streaming.py`
- Modify: `src/voice_assistant/cli.py` — `_run_gui_mode._do_request` uses streaming speaker

- [ ] **Step 1: Failing test**

```python
# tests/test_tts_streaming.py
from voice_assistant.tts.streaming import sentence_chunks


def test_sentence_chunks_splits_on_punctuation():
    chunks = list(sentence_chunks("Hello. How are you? I'm fine!"))
    assert chunks == ["Hello.", "How are you?", "I'm fine!"]


def test_sentence_chunks_handles_streaming_input():
    """Feed the chunker token-by-token and verify it emits sentences only when complete."""
    from voice_assistant.tts.streaming import StreamingSentenceChunker
    s = StreamingSentenceChunker()
    out = []
    for piece in ["Hello", " there", ".", " How", " are", " you", "?"]:
        out.extend(s.feed(piece))
    out.extend(s.flush())
    assert out == ["Hello there.", "How are you?"]


def test_sentence_chunks_handles_no_terminal_punctuation():
    from voice_assistant.tts.streaming import StreamingSentenceChunker
    s = StreamingSentenceChunker()
    s.feed("This has no terminal punctuation")
    assert list(s.flush()) == ["This has no terminal punctuation"]
```

- [ ] **Step 2: Implement `tts/streaming.py`**

```python
"""Stream LLM text → sentence chunks → TTS playback queue.

Used by the orchestrator's stream path: we feed each `assistant_delta` text
chunk into a `StreamingSentenceChunker`. Whenever a sentence completes, it's
queued for synthesis on a background thread, and the chunker carries on
buffering the next.
"""
from __future__ import annotations
import logging
import queue
import re
import threading
from collections.abc import Iterator

from voice_assistant.tts.base import Speaker

log = logging.getLogger(__name__)


_SENTENCE_END = re.compile(r"([.!?]+)(\s|$)")


def sentence_chunks(text: str) -> Iterator[str]:
    """Split a complete string into sentences, preserving punctuation."""
    pos = 0
    for m in _SENTENCE_END.finditer(text):
        end = m.end(1)
        chunk = text[pos:end].strip()
        if chunk:
            yield chunk
        pos = m.end()
    tail = text[pos:].strip()
    if tail:
        yield tail


class StreamingSentenceChunker:
    """Streaming variant: feed it text incrementally, get sentences as they complete."""

    def __init__(self) -> None:
        self._buf = ""

    def feed(self, text: str) -> list[str]:
        self._buf += text
        out: list[str] = []
        while True:
            m = _SENTENCE_END.search(self._buf)
            if not m:
                break
            end = m.end(1)
            sentence = self._buf[:end].strip()
            self._buf = self._buf[m.end():]
            if sentence:
                out.append(sentence)
        return out

    def flush(self) -> list[str]:
        tail = self._buf.strip()
        self._buf = ""
        return [tail] if tail else []


class SentenceQueueSpeaker:
    """Wraps a Speaker. `enqueue(text)` adds to the playback queue.
    Synthesis + playback happen on a background thread, sequential.
    `wait()` blocks until the queue is drained.
    """

    _SENTINEL = object()

    def __init__(self, speaker: Speaker) -> None:
        self._speaker = speaker
        self._q: queue.Queue = queue.Queue()
        self._chunker = StreamingSentenceChunker()
        self._thread = threading.Thread(target=self._run, daemon=True, name="va-tts")
        self._thread.start()

    def feed(self, text_delta: str) -> None:
        for sentence in self._chunker.feed(text_delta):
            self._q.put(sentence)

    def flush(self) -> None:
        for sentence in self._chunker.flush():
            self._q.put(sentence)
        self._q.put(self._SENTINEL)

    def wait(self) -> None:
        self._q.join()

    def _run(self) -> None:
        while True:
            item = self._q.get()
            try:
                if item is self._SENTINEL:
                    return
                try:
                    self._speaker.speak(item)
                except Exception:
                    log.exception("speaker.speak failed for sentence")
            finally:
                self._q.task_done()
```

- [ ] **Step 3: Wire into `cli.py`**

In `_run_gui_mode._do_request`, replace the existing post-stream `speaker.speak(buf)` block with a sentence-streaming pattern:

```python
from voice_assistant.tts.streaming import SentenceQueueSpeaker
from voice_assistant.tts import make_speaker

# Build streaming speaker once, reuse per request
streaming_speaker = SentenceQueueSpeaker(make_speaker(voice_id=cfg.tts.voice)) if cfg.audio.trigger == "hotkey" else None

def _do_request(text: str) -> None:
    history.append("user", text)
    bus.publish({"type": "transcript", "speaker": "user", "text": text})
    bus.publish({"type": "status", "value": "thinking"})
    buf = ""
    speaker_for_request = SentenceQueueSpeaker(make_speaker(voice_id=state["cfg"].tts.voice)) \
        if state["cfg"].audio.trigger == "hotkey" else None
    try:
        bus.publish({"type": "transcript_start", "speaker": "assistant"})
        for ev in state["orch"].handle_stream(text):
            if ev["type"] == "assistant_delta":
                buf += ev["text"]
                bus.publish({"type": "transcript_chunk", "text": ev["text"]})
                if speaker_for_request is not None:
                    bus.publish({"type": "status", "value": "speaking"})
                    speaker_for_request.feed(ev["text"])
            elif ev["type"] == "tool_invoked":
                bus.publish({"type": "tool_invoked", "name": ev["name"]})
            elif ev["type"] == "done":
                if speaker_for_request is not None:
                    speaker_for_request.flush()
                    speaker_for_request.wait()
                history.append("assistant", buf)
                bus.publish({"type": "transcript_end"})
    except Exception as exc:
        log.exception("orch.handle_stream failed")
        if speaker_for_request is not None:
            speaker_for_request.flush()
        bus.publish({"type": "transcript_end"})
        bus.publish({"type": "toast", "level": "error", "message": str(exc)})
        bus.publish({"type": "status", "value": "error"})
    finally:
        bus.publish({"type": "status", "value": "idle"})
```

(Per-request speaker so each request is isolated. The constructor cost is dominated by the synth call, not the constructor itself; a one-off `make_speaker` is fine.)

- [ ] **Step 4: Tests**

```bash
~/.local/share/voice-assistant/.venv/bin/pytest tests/test_tts_streaming.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/voice_assistant/tts/streaming.py tests/test_tts_streaming.py src/voice_assistant/cli.py
git commit -m "feat(tts): sentence-streaming TTS — speak first sentence while generating rest"
```

---

## Task 4: System prompt — respond in user's language

**Files:**
- Modify: `src/voice_assistant/brain.py` — `_build_system_prompt`

- [ ] **Step 1: Add a language line to the system prompt**

Find the existing `_build_system_prompt` and add this rule:

```python
"Always respond in the same language the user used. If they switch languages mid-conversation, switch with them. Do not translate unless asked.\n"
```

- [ ] **Step 2: Add a test**

```python
def test_system_prompt_includes_language_rule():
    p = _build_system_prompt(UserConfig(name="Zeeshan", address_as="first_name"))
    assert "language" in p.lower()
```

- [ ] **Step 3: Commit**

```bash
git add src/voice_assistant/brain.py tests/test_brain.py
git commit -m "feat(brain): system prompt instructs respond-in-user-language"
```

---

## Task 5: Default to faster models

**Files:**
- Modify: `src/voice_assistant/setup_wizard.py` — DEFAULT_MODELS

- [ ] **Step 1: Update DEFAULT_MODELS**

```python
DEFAULT_MODELS: dict[Provider, str] = {
    "anthropic": "claude-haiku-4-5",     # was claude-sonnet-4-6 — haiku is ~3-4× faster
    "openai":    "gpt-5.4-mini",         # was gpt-5.5
    "gemini":    "gemini-3.1-flash",     # was gemini-3.1-pro
    "ollama":    "qwen3:14b",
}
```

The full lists in `MODELS_BY_PROVIDER` already include both fast and capable models — the user can swap to the bigger model in Settings whenever they want depth over speed. The default just optimises for the common case (chat, simple commands).

- [ ] **Step 2: Update wizard tests**

The existing tests use `claude-sonnet-4-6` as a default check. Update them to expect `claude-haiku-4-5`.

- [ ] **Step 3: Commit**

```bash
git add src/voice_assistant/setup_wizard.py tests/test_setup_wizard.py
git commit -m "feat(brain): default to faster models per provider (haiku / mini / flash)"
```

---

## Task 6: Animated avatar component (replaces Orb as centerpiece)

**Files:**
- Create: `web/public/avatars/aria.svg`
- Create: `web/public/avatars/liam.svg`
- Create: `web/public/avatars/sage.svg`
- Create: `web/src/components/Avatar.ts`
- Modify: `web/src/main.ts` — replace Orb mount

- [ ] **Step 1: Generate SVG avatars from DiceBear**

DiceBear is permissively licensed. Use the bottts and avataaars styles. Run from a shell that has internet:

```bash
mkdir -p /home/zeeshan-ahmed/voice-assistant/web/public/avatars
curl -fsSL "https://api.dicebear.com/9.x/avataaars/svg?seed=aria&backgroundColor=9580ff,7c5cff,c0a8ff&radius=50" -o /home/zeeshan-ahmed/voice-assistant/web/public/avatars/aria.svg
curl -fsSL "https://api.dicebear.com/9.x/avataaars/svg?seed=liam&backgroundColor=34d399,2dd4bf,4ade80&radius=50" -o /home/zeeshan-ahmed/voice-assistant/web/public/avatars/liam.svg
curl -fsSL "https://api.dicebear.com/9.x/avataaars/svg?seed=sage&backgroundColor=f59e0b,fb923c,fbbf24&radius=50" -o /home/zeeshan-ahmed/voice-assistant/web/public/avatars/sage.svg
```

(If DiceBear is unreachable, fall back to `bottts` style with the same seeds, or hand-craft three simple SVG circles with stylised faces. The aesthetic isn't critical — variety is.)

- [ ] **Step 2: Create `web/src/components/Avatar.ts`**

```ts
export type AvatarState = 'idle'|'listening'|'thinking'|'speaking'|'error';

const AVATAR_SRC: Record<string, string> = {
  aria: '/avatars/aria.svg',
  liam: '/avatars/liam.svg',
  sage: '/avatars/sage.svg',
};

export class Avatar {
  private el: HTMLElement;
  private img: HTMLImageElement;
  private halo: HTMLElement;
  private dots: HTMLElement;
  private state: AvatarState = 'idle';

  constructor(parent: HTMLElement, initialAvatar = 'aria') {
    this.el = document.createElement('div');
    this.el.className = 'flex-1 grid place-items-center relative';
    this.el.innerHTML = `
      <div data-halo class="absolute h-72 w-72 rounded-full opacity-0 transition-opacity duration-300"
        style="background: radial-gradient(closest-side, rgba(149,128,255,0.45), transparent 70%); filter: blur(40px);"></div>
      <img data-img alt="assistant avatar" class="relative h-56 w-56 rounded-full object-cover shadow-2xl shadow-black/40 border-2 border-border"
        style="background: linear-gradient(135deg, #1f242c, #0b0d10);" />
      <div data-dots class="absolute -top-4 hidden gap-1.5">
        <span class="block h-2 w-2 rounded-full bg-accent animate-bounce"></span>
        <span class="block h-2 w-2 rounded-full bg-accent animate-bounce" style="animation-delay: 0.15s"></span>
        <span class="block h-2 w-2 rounded-full bg-accent animate-bounce" style="animation-delay: 0.30s"></span>
      </div>
      <p data-hint class="absolute bottom-12 text-sm text-muted">Press the hotkey to talk</p>
    `;
    parent.appendChild(this.el);
    this.img = this.el.querySelector<HTMLImageElement>('[data-img]')!;
    this.halo = this.el.querySelector<HTMLElement>('[data-halo]')!;
    this.dots = this.el.querySelector<HTMLElement>('[data-dots]')!;
    this.setAvatar(initialAvatar);
    this.startBreathing();
  }

  setAvatar(name: string): void {
    const src = AVATAR_SRC[name] ?? AVATAR_SRC['aria'];
    this.img.src = src;
  }

  setState(s: AvatarState): void {
    this.state = s;
    const hint = this.el.querySelector<HTMLElement>('[data-hint]')!;
    hint.textContent = {
      idle:      'Press the hotkey to talk',
      listening: 'Listening…',
      thinking:  'Thinking…',
      speaking:  '',
      error:     'Something went wrong.',
    }[s];

    // Halo intensity per state
    const haloClass = (op: string) => { this.halo.style.opacity = op; };
    haloClass(s === 'listening' || s === 'speaking' ? '1' :
              s === 'thinking' ? '0.4' :
              s === 'error' ? '0' : '0.6');

    // Thinking dots
    this.dots.classList.toggle('hidden', s !== 'thinking');
    this.dots.classList.toggle('flex', s === 'thinking');

    // Bobbing intensity
    if (s === 'speaking') {
      this.img.style.animation = 'va-bob 0.4s ease-in-out infinite alternate';
    } else if (s === 'listening') {
      this.img.style.animation = 'va-bob 1.2s ease-in-out infinite alternate';
    } else {
      this.img.style.animation = 'va-breathe 4s ease-in-out infinite';
    }
  }

  setRms(_v: number): void {
    // Reserved for future audio-reactive scaling.
  }

  private startBreathing(): void {
    if (!document.querySelector('#va-avatar-keyframes')) {
      const style = document.createElement('style');
      style.id = 'va-avatar-keyframes';
      style.textContent = `
        @keyframes va-breathe { 0%,100% { transform: scale(1); } 50% { transform: scale(1.02); } }
        @keyframes va-bob { 0% { transform: translateY(0); } 100% { transform: translateY(-4px); } }
        @media (prefers-reduced-motion: reduce) {
          [data-img] { animation: none !important; }
        }
      `;
      document.head.appendChild(style);
    }
  }

  destroy(): void { /* no-op (CSS animations stop with element removal) */ }
}
```

- [ ] **Step 3: Replace Orb with Avatar in `web/src/main.ts`**

```ts
import { Avatar } from './components/Avatar';
// remove or keep: import { Orb } from './components/Orb';

const avatar = new Avatar(root, currentConfig?.avatar ?? 'aria');
// keep transcript constraint code below

bus.on((e) => {
  switch (e.type) {
    case 'status':
      header.setStatus(e.value);
      avatar.setState(e.value);
      break;
    // ...
    case 'audio_level':
      avatar.setRms(e.rms);
      break;
    case 'config':
      currentConfig = e.cfg;
      avatar.setAvatar(currentConfig.avatar ?? 'aria');
      break;
    // ...
  }
});
```

- [ ] **Step 4: Build, smoke**

```bash
cd web && npm run build
```

- [ ] **Step 5: Commit**

```bash
git add web/public/avatars/ web/src/components/Avatar.ts web/src/main.ts src/voice_assistant/desktop/web_dist/
git commit -m "feat(desktop): animated avatar centerpiece (Aria / Liam / Sage)"
```

---

## Task 7: Settings drawer — voice + avatar + STT language pickers

**Files:**
- Modify: `src/voice_assistant/desktop/bridge.py` — return voices, avatars, STT languages
- Modify: `web/src/types.ts`
- Modify: `web/src/components/Settings.ts`

- [ ] **Step 1: Bridge — add catalog data to `get_config`**

```python
from voice_assistant.voice_catalog import VOICES, STT_LANGUAGES

def get_config(self) -> dict[str, Any]:
    cfg = _config_to_dict(self._config_path) or _default_config_dict()
    cfg["has_secret"] = _has_secret_for(cfg["provider"], self._env_path)
    cfg["available_models"] = {p: list(m) for p, m in MODELS_BY_PROVIDER.items()}
    cfg["available_voices"] = [
        {"id": v.id, "label": v.label, "language": v.language, "gender": v.gender, "engine": v.engine, "notes": v.notes}
        for v in VOICES
    ]
    cfg["available_stt_languages"] = [{"code": c, "label": l} for c, l in STT_LANGUAGES]
    cfg["available_avatars"] = ["aria", "liam", "sage"]
    return cfg
```

Also include the persisted voice + avatar in `_config_to_dict`:

```python
"voice":         cfg.tts.voice,
"stt_language":  cfg.stt.language,
"avatar":        getattr(cfg, "avatar", "aria"),  # see Task 8 for AppConfig.avatar
```

- [ ] **Step 2: Types**

```ts
export interface AppConfig {
  // ...existing fields...
  voice: string;
  stt_language: string;
  avatar: string;
  available_voices?: { id: string; label: string; language: string; gender: string; engine: string; notes: string }[];
  available_stt_languages?: { code: string; label: string }[];
  available_avatars?: string[];
}
```

- [ ] **Step 3: Settings drawer — three new sections**

Add after the existing fields, before the Identity section:

```html
<div class="border-t border-border pt-5 space-y-3">
  <h3 class="font-medium text-fg">Voice</h3>
  <div>
    <label class="block text-muted mb-1">Avatar</label>
    <div data-field="avatar" class="grid grid-cols-3 gap-2"></div>
  </div>
  <div>
    <label class="block text-muted mb-1">Voice</label>
    <select data-field="voice" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg"></select>
    <button type="button" data-test-voice
      class="mt-2 text-xs text-accent hover:underline">▶ Test this voice</button>
  </div>
  <div>
    <label class="block text-muted mb-1">Speech recognition language</label>
    <select data-field="stt_language" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg"></select>
  </div>
</div>
```

In `populate`, build the avatar grid (clickable buttons), the voice dropdown (grouped by language), and the STT language dropdown.

```ts
private refreshVoiceSection(): void {
  // Avatars
  const avatars = this.currentCfg?.available_avatars ?? ['aria','liam','sage'];
  const grid = this.el.querySelector<HTMLElement>('[data-field="avatar"]')!;
  grid.innerHTML = '';
  for (const name of avatars) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'rounded-md border-2 border-border p-2 hover:border-accent transition-colors aria-pressed:border-accent';
    btn.dataset.avatar = name;
    btn.setAttribute('aria-pressed', String(name === (this.currentCfg?.avatar ?? 'aria')));
    btn.innerHTML = `<img src="/avatars/${name}.svg" alt="${name}" class="h-16 w-16 mx-auto rounded-full" />
      <p class="mt-1 text-xs capitalize text-center">${name}</p>`;
    btn.addEventListener('click', () => {
      grid.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', 'false'));
      btn.setAttribute('aria-pressed', 'true');
    });
    grid.appendChild(btn);
  }

  // Voices grouped by language
  const voices = this.currentCfg?.available_voices ?? [];
  const select = this.el.querySelector<HTMLSelectElement>('[data-field="voice"]')!;
  select.innerHTML = '';
  const byLang: Record<string, typeof voices> = {};
  for (const v of voices) (byLang[v.language] ??= []).push(v);
  // Stable ordering: English first, then alphabetical by language label
  const langOrder = Object.keys(byLang).sort((a, b) => a === 'en' ? -1 : b === 'en' ? 1 : a.localeCompare(b));
  for (const lang of langOrder) {
    const og = document.createElement('optgroup');
    og.label = byLang[lang][0].label.match(/\(([^)]+)\)/)?.[1] || lang;
    for (const v of byLang[lang]) {
      const opt = document.createElement('option');
      opt.value = v.id;
      opt.textContent = `${v.label}${v.notes ? ' · ' + v.notes : ''}`;
      og.appendChild(opt);
    }
    select.appendChild(og);
  }
  if (this.currentCfg?.voice) select.value = this.currentCfg.voice;

  // STT languages
  const sttLangs = this.currentCfg?.available_stt_languages ?? [];
  const sttSelect = this.el.querySelector<HTMLSelectElement>('[data-field="stt_language"]')!;
  sttSelect.innerHTML = '';
  for (const l of sttLangs) {
    const opt = document.createElement('option');
    opt.value = l.code;
    opt.textContent = l.label;
    sttSelect.appendChild(opt);
  }
  if (this.currentCfg?.stt_language) sttSelect.value = this.currentCfg.stt_language;
}
```

In `read`, include the new fields:

```ts
const voice = (this.el.querySelector('[data-field="voice"]') as HTMLSelectElement).value;
const stt_language = (this.el.querySelector('[data-field="stt_language"]') as HTMLSelectElement).value;
const avatar = (this.el.querySelector('[data-field="avatar"] [aria-pressed="true"]') as HTMLElement)?.dataset.avatar ?? 'aria';
return { ..., voice, stt_language, avatar };
```

In bridge.save_config, accept these fields and persist them.

- [ ] **Step 4: Build, smoke**

```bash
cd web && npm run build
```

- [ ] **Step 5: Commit**

```bash
git add src/voice_assistant/desktop/bridge.py web/src/types.ts web/src/components/Settings.ts src/voice_assistant/desktop/web_dist/
git commit -m "feat(desktop): voice + avatar + STT language pickers in settings"
```

---

## Task 8: Persist voice/avatar/stt_language through wizard + render_config

**Files:**
- Modify: `src/voice_assistant/setup_wizard.py` — WizardAnswers + render_config

- [ ] **Step 1: Extend WizardAnswers**

```python
@dataclass(frozen=True)
class WizardAnswers:
    # ...existing fields...
    voice: str = "piper:en_US-amy-medium"
    stt_language: str = "auto"
    avatar: str = "aria"
```

- [ ] **Step 2: render_config emits the new fields**

```yaml
stt:
  engine: faster-whisper
  model: small
  language: {stt_language}
tts:
  engine: piper           # legacy; engine is derived from voice id
  voice: {voice}
```

(Engine is inferred from the `voice:` prefix at runtime. For backward compat we keep the `engine:` line but it's effectively unused.)

Avatar lives at the top level (it's UI metadata, not config the engine reads):

```yaml
avatar: {avatar}
```

Add `Config.avatar: str = "aria"` so old configs still validate.

- [ ] **Step 3: Wizard prompts for voice + STT language at the end (optional — skip-able)**

```python
voice = _prompt_with_default("\n7) Voice (e.g. openai:nova for premium multilingual)", "piper:en_US-amy-medium")
stt_lang = _prompt_with_default("\n8) Speech recognition language (auto, en, ur, hi, …)", "auto")
```

(Most users will edit these in Settings later; defaults are fine for first run.)

- [ ] **Step 4: Tests**

Add to `test_user_config.py`:

```python
def test_render_config_includes_voice_and_stt_language():
    yaml_text = render_config(_ans(voice="openai:nova", stt_language="ur"))
    cfg = Config.model_validate(yaml.safe_load(yaml_text))
    assert cfg.tts.voice == "openai:nova"
    assert cfg.stt.language == "ur"
```

- [ ] **Step 5: Commit**

```bash
git add src/voice_assistant/setup_wizard.py src/voice_assistant/config.py tests/
git commit -m "feat(config): persist voice + STT language + avatar"
```

---

## Task 9: Verify + push

- [ ] **Step 1: Full pytest**

```bash
~/.local/share/voice-assistant/.venv/bin/pytest -q
```

Expected: all tests still pass, ~10-15 new ones.

- [ ] **Step 2: Lint + types**

```bash
~/.local/share/voice-assistant/.venv/bin/ruff check src/ tests/
~/.local/share/voice-assistant/.venv/bin/mypy src/voice_assistant
```

- [ ] **Step 3: Web build**

```bash
cd web && npm run build
```

- [ ] **Step 4: Reinstall + smoke**

```bash
~/.local/share/voice-assistant/.venv/bin/pip install -e /home/zeeshan-ahmed/voice-assistant --no-deps
~/.local/share/voice-assistant/.venv/bin/pip install openai soundfile  # OpenAI TTS deps
pkill -f "voice-assistant --gui" 2>/dev/null; sleep 1
DISPLAY=:0 ~/.local/share/voice-assistant/.venv/bin/voice-assistant --gui --config ~/.voice-assistant/config.yaml &
```

In the GUI: Settings → switch voice to `openai:nova`, switch avatar to `liam`, save. Send a message in Urdu. The avatar should change to Liam's portrait, and the response should be spoken in Urdu by Nova.

- [ ] **Step 5: Push**

```bash
git push origin main
```

---

## Done criteria

- `pytest -q` passes (~170+ tests).
- The GUI shows an animated SVG avatar (default Aria) instead of the orb.
- Settings → Voice section lets you pick from 30+ voices grouped by language and 3 avatars.
- STT language can be set to `auto`, `en`, `ur`, `hi`, `cs`, `sk`, etc — and faster-whisper transcribes accordingly.
- Sending a message in Urdu produces a response in Urdu (assistant follows user's language).
- Time-to-first-audio drops from "after the full reply" to "after the first sentence" because of streaming TTS.
- Default model is faster (haiku/mini/flash); user can switch to bigger model in Settings.
