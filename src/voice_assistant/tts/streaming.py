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
            self._buf = self._buf[m.end() :]
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
        self._q: queue.Queue[object] = queue.Queue()
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
                    self._speaker.speak(str(item))
                except Exception:
                    log.exception("speaker.speak failed for sentence")
            finally:
                self._q.task_done()
