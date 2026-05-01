"""Tests for multi-modal image input (Item 24).

The tests verify that:
  1. Orchestrator.handle_stream correctly builds multi-modal content blocks
     when images are present.
  2. The brain receives the expected message shape (text + image_url blocks).
  3. When no images are given the content remains a plain string.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from voice_assistant.app import Orchestrator
from voice_assistant.brain import Brain, ContentChunk

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_DATA_URL = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="


def _make_orch() -> Orchestrator:
    brain = MagicMock(spec=Brain)
    brain.complete_stream = MagicMock(return_value=iter([ContentChunk(text="ok")]))
    return Orchestrator(brain=brain, tools=[])


# ---------------------------------------------------------------------------
# Unit: _build_user_content
# ---------------------------------------------------------------------------


class TestBuildUserContent:
    def test_plain_text_when_no_images(self):
        content = Orchestrator._build_user_content("hello", [])
        assert content == "hello"

    def test_content_blocks_when_images_present(self):
        content = Orchestrator._build_user_content("describe", [_FAKE_DATA_URL])
        assert isinstance(content, list)
        assert content[0] == {"type": "text", "text": "describe"}
        assert content[1] == {
            "type": "image_url",
            "image_url": {"url": _FAKE_DATA_URL},
        }

    def test_multiple_images(self):
        imgs = [_FAKE_DATA_URL, _FAKE_DATA_URL]
        content = Orchestrator._build_user_content("compare", imgs)
        assert len(content) == 3  # 1 text + 2 images
        assert content[0]["type"] == "text"
        assert content[1]["type"] == "image_url"
        assert content[2]["type"] == "image_url"


# ---------------------------------------------------------------------------
# Integration: handle_stream passes correct message shape to brain
# ---------------------------------------------------------------------------


class TestHandleStreamImageShape:
    def test_no_images_sends_string_content(self):
        orch = _make_orch()
        list(orch.handle_stream("hi"))
        captured = orch.brain.complete_stream.call_args
        messages = captured[0][0]  # first positional arg
        user_msg = next(m for m in messages if m["role"] == "user")
        assert user_msg["content"] == "hi"

    def test_with_image_sends_block_list(self):
        orch = _make_orch()
        # Reset the mock so complete_stream returns a fresh iterator each call
        orch.brain.complete_stream.side_effect = lambda msgs, tools, **_kw: iter(
            [ContentChunk(text="described")]
        )
        list(orch.handle_stream("describe this", images=[_FAKE_DATA_URL]))
        captured = orch.brain.complete_stream.call_args
        messages = captured[0][0]
        user_msg = next(m for m in messages if m["role"] == "user")
        content = user_msg["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "text"
        assert content[1]["type"] == "image_url"
        assert _FAKE_DATA_URL in content[1]["image_url"]["url"]

    def test_stream_events_still_emitted_with_images(self):
        orch = _make_orch()
        orch.brain.complete_stream.side_effect = lambda msgs, tools, **_kw: iter(
            [ContentChunk(text="sure")]
        )
        events = list(orch.handle_stream("look", images=[_FAKE_DATA_URL]))
        types = [e["type"] for e in events]
        assert "assistant_delta" in types
        assert "done" in types

    def test_empty_images_list_treated_as_no_images(self):
        orch = _make_orch()
        list(orch.handle_stream("hello", images=[]))
        captured = orch.brain.complete_stream.call_args
        messages = captured[0][0]
        user_msg = next(m for m in messages if m["role"] == "user")
        # Should still be a plain string
        assert isinstance(user_msg["content"], str)
