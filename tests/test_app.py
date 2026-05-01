"""Tests for Orchestrator.handle_stream with history and auto-recall."""
from __future__ import annotations

from unittest.mock import MagicMock

from voice_assistant.app import Orchestrator
from voice_assistant.tools.schema import ToolResult, ToolSpec


def _make_orch(brain: MagicMock, tools: list[ToolSpec] | None = None) -> Orchestrator:
    return Orchestrator(brain=brain, tools=tools or [])


def _plain_brain() -> MagicMock:
    """Brain that returns no chunks (empty stream)."""
    b = MagicMock()
    b.complete_stream.return_value = iter([])
    return b


# ---------------------------------------------------------------------------
# Task 1: history threading
# ---------------------------------------------------------------------------


def test_handle_stream_includes_history_in_messages():
    """Past turns are formatted as user/assistant messages and prepended."""
    brain = _plain_brain()
    orch = _make_orch(brain)
    history = [
        {"speaker": "user", "text": "what's the time?"},
        {"speaker": "assistant", "text": "It's 3pm."},
    ]
    list(orch.handle_stream("what was my last question?", history=history))
    args, kwargs = brain.complete_stream.call_args
    messages = args[0] if args else kwargs.get("messages")
    # First two are history (user, assistant), last is current
    assert len(messages) == 3
    assert messages[0] == {"role": "user", "content": "what's the time?"}
    assert messages[1] == {"role": "assistant", "content": "It's 3pm."}
    assert messages[2] == {"role": "user", "content": "what was my last question?"}


def test_handle_stream_no_history_sends_only_current_turn():
    """Without history kwarg, only the current user turn is sent."""
    brain = _plain_brain()
    orch = _make_orch(brain)
    list(orch.handle_stream("hello"))
    args, kwargs = brain.complete_stream.call_args
    messages = args[0] if args else kwargs.get("messages")
    assert len(messages) == 1
    assert messages[0] == {"role": "user", "content": "hello"}


def test_handle_stream_history_none_is_backward_compat():
    """history=None is equivalent to no history — only current turn."""
    brain = _plain_brain()
    orch = _make_orch(brain)
    list(orch.handle_stream("ping", history=None))
    args, kwargs = brain.complete_stream.call_args
    messages = args[0] if args else kwargs.get("messages")
    assert len(messages) == 1


def test_handle_stream_caps_history_by_char_budget():
    """Old turns are dropped when their text exceeds the 4000-char budget."""
    brain = _plain_brain()
    orch = _make_orch(brain)
    # Single entry of 5 000 chars — over the 4 000 char budget
    long_history = [{"speaker": "user", "text": "X" * 5000}]
    list(orch.handle_stream("hi", history=long_history))
    args, kwargs = brain.complete_stream.call_args
    messages = args[0] if args else kwargs.get("messages")
    # The long entry should be dropped; only the current turn remains
    assert len(messages) == 1
    assert messages[0] == {"role": "user", "content": "hi"}


def test_handle_stream_history_replayed_chronologically():
    """History is replayed oldest-first (chronological) regardless of walk order."""
    brain = _plain_brain()
    orch = _make_orch(brain)
    history = [
        {"speaker": "user", "text": "first"},
        {"speaker": "assistant", "text": "second"},
        {"speaker": "user", "text": "third"},
    ]
    list(orch.handle_stream("fourth", history=history))
    args, kwargs = brain.complete_stream.call_args
    messages = args[0] if args else kwargs.get("messages")
    assert [m["content"] for m in messages] == ["first", "second", "third", "fourth"]


def test_handle_stream_history_unknown_speaker_becomes_assistant():
    """Any speaker that isn't 'user' is mapped to 'assistant'."""
    brain = _plain_brain()
    orch = _make_orch(brain)
    history = [{"speaker": "system_bot", "text": "notice"}]
    list(orch.handle_stream("ok", history=history))
    args, kwargs = brain.complete_stream.call_args
    messages = args[0] if args else kwargs.get("messages")
    assert messages[0]["role"] == "assistant"


def test_handle_stream_history_fits_within_budget():
    """Multiple entries that fit within budget are all included."""
    brain = _plain_brain()
    orch = _make_orch(brain)
    history = [
        {"speaker": "user", "text": "a" * 1000},
        {"speaker": "assistant", "text": "b" * 1000},
        {"speaker": "user", "text": "c" * 1000},
    ]
    list(orch.handle_stream("now", history=history))
    args, kwargs = brain.complete_stream.call_args
    messages = args[0] if args else kwargs.get("messages")
    # 3 000 chars < 4 000 budget, so all three history entries + current turn
    assert len(messages) == 4


# ---------------------------------------------------------------------------
# Task 2: auto-recall
# ---------------------------------------------------------------------------


def _make_recall_spec(return_facts: list[dict]) -> ToolSpec:
    """Build a fake 'recall' ToolSpec."""

    def _recall_fn(**kwargs: object) -> ToolResult:
        return ToolResult(ok=True, summary="recalled", data={"results": return_facts})

    return ToolSpec(
        name="recall",
        description="recall facts",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
        func=_recall_fn,
    )


def test_handle_stream_auto_recalls_relevant_facts():
    """When recall tool exists, results are prepended to system prompt as extra_ctx."""
    brain = _plain_brain()
    facts = [{"text": "User's name is Alice", "id": "1"}]
    orch = _make_orch(brain, tools=[_make_recall_spec(facts)])
    list(orch.handle_stream("who am I?"))
    _, kwargs = brain.complete_stream.call_args
    extra_ctx = kwargs.get("extra_system_context")
    assert extra_ctx is not None
    assert "Alice" in extra_ctx
    assert "Known facts about the user" in extra_ctx


def test_handle_stream_no_recall_tool_passes_no_extra_context():
    """When no recall tool is registered, extra_system_context is None."""
    brain = _plain_brain()
    orch = _make_orch(brain, tools=[])
    list(orch.handle_stream("hello"))
    _, kwargs = brain.complete_stream.call_args
    extra_ctx = kwargs.get("extra_system_context")
    assert extra_ctx is None


def test_handle_stream_empty_recall_results_no_extra_context():
    """When recall returns no results, extra_system_context stays None."""
    brain = _plain_brain()
    orch = _make_orch(brain, tools=[_make_recall_spec([])])
    list(orch.handle_stream("hello"))
    _, kwargs = brain.complete_stream.call_args
    extra_ctx = kwargs.get("extra_system_context")
    assert extra_ctx is None


def test_handle_stream_recall_failure_does_not_block_request():
    """If recall raises, the request still completes and extra_ctx is None."""

    def _bad_recall(**kwargs: object) -> ToolResult:
        raise RuntimeError("embedding service down")

    bad_spec = ToolSpec(
        name="recall",
        description="recall facts",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
        func=_bad_recall,
    )
    brain = _plain_brain()
    orch = _make_orch(brain, tools=[bad_spec])
    # Must not raise
    events = list(orch.handle_stream("hi"))
    assert any(e["type"] == "done" for e in events)
    _, kwargs = brain.complete_stream.call_args
    extra_ctx = kwargs.get("extra_system_context")
    assert extra_ctx is None


def test_handle_stream_recall_formats_multiple_facts():
    """Multiple facts produce a bulleted list in extra_ctx."""
    brain = _plain_brain()
    facts = [
        {"text": "User likes chess", "id": "1"},
        {"text": "User is from Pakistan", "id": "2"},
        {"text": "User prefers dark mode", "id": "3"},
    ]
    orch = _make_orch(brain, tools=[_make_recall_spec(facts)])
    list(orch.handle_stream("what do you know?"))
    _, kwargs = brain.complete_stream.call_args
    extra_ctx = kwargs.get("extra_system_context")
    assert extra_ctx is not None
    assert "chess" in extra_ctx
    assert "Pakistan" in extra_ctx
    assert "dark mode" in extra_ctx
    # Each fact on its own line with a dash
    lines = [ln for ln in extra_ctx.splitlines() if ln.strip().startswith("-")]
    assert len(lines) == 3


# ---------------------------------------------------------------------------
# Task 2b: Brain.complete_stream — extra_system_context
# ---------------------------------------------------------------------------


def test_brain_complete_stream_appends_extra_system_context(monkeypatch):
    """extra_system_context is appended to the auto-built system message."""
    from voice_assistant.brain import Brain

    captured: list[list] = []

    def _fake_completion(**kwargs):  # type: ignore[no-untyped-def]
        captured.append(kwargs["messages"])
        return iter([])  # no chunks

    monkeypatch.setattr("voice_assistant.brain.litellm.completion", _fake_completion)
    brain = Brain(provider="anthropic", model="claude-sonnet-4-6")
    list(
        brain.complete_stream(
            [{"role": "user", "content": "hi"}],
            tools=[],
            extra_system_context="Known facts:\n  - User likes tea",
        )
    )
    msgs = captured[0]
    assert msgs[0]["role"] == "system"
    assert "Known facts" in msgs[0]["content"]
    assert "User likes tea" in msgs[0]["content"]


def test_brain_complete_stream_no_extra_context_unchanged(monkeypatch):
    """Without extra_system_context the system prompt is unchanged."""
    from voice_assistant.brain import Brain, _build_system_prompt

    captured: list[list] = []

    def _fake_completion(**kwargs):  # type: ignore[no-untyped-def]
        captured.append(kwargs["messages"])
        return iter([])

    monkeypatch.setattr("voice_assistant.brain.litellm.completion", _fake_completion)
    brain = Brain(provider="anthropic", model="claude-sonnet-4-6")
    list(brain.complete_stream([{"role": "user", "content": "hi"}], tools=[]))
    msgs = captured[0]
    assert msgs[0]["content"] == _build_system_prompt(None)
