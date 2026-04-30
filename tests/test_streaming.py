from unittest.mock import MagicMock
from voice_assistant.brain import Brain, ContentChunk, ToolCallReady


def test_brain_complete_stream_emits_text_chunks(monkeypatch):
    """Brain.complete_stream yields ContentChunk for plain text deltas."""
    fake_chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="Hel", tool_calls=None))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="lo!", tool_calls=None))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content=None, tool_calls=None))]),
    ]
    monkeypatch.setattr("voice_assistant.brain.litellm.completion", lambda **kw: iter(fake_chunks))
    brain = Brain(provider="anthropic", model="claude-sonnet-4-6")
    out = list(brain.complete_stream([{"role": "user", "content": "hi"}], tools=[]))
    texts = [c.text for c in out if isinstance(c, ContentChunk)]
    assert "".join(texts) == "Hello!"


def test_brain_complete_stream_assembles_tool_call(monkeypatch):
    """Tool-call deltas are accumulated into a single ToolCallReady at completion."""
    # Simulated tool_call deltas across two chunks.
    # Note: MagicMock(name=...) sets the mock's display name, NOT an attribute.
    # Use explicit attribute assignment to set function.name and function.arguments.
    fn1 = MagicMock()
    fn1.name = "get_weather"
    fn1.arguments = '{"city":"S'
    tc1 = MagicMock(index=0, id="call_1")
    tc1.function = fn1

    fn2 = MagicMock()
    fn2.name = None  # no name in second chunk (argument continuation only)
    fn2.arguments = 'F"}'
    tc2 = MagicMock(index=0, id=None)
    tc2.function = fn2

    fake_chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content=None, tool_calls=[tc1]))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content=None, tool_calls=[tc2]))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content=None, tool_calls=None))]),
    ]
    monkeypatch.setattr("voice_assistant.brain.litellm.completion", lambda **kw: iter(fake_chunks))
    brain = Brain(provider="openai", model="gpt-5.5")
    out = list(brain.complete_stream([{"role": "user", "content": "weather"}], tools=[]))
    tools = [c for c in out if isinstance(c, ToolCallReady)]
    assert len(tools) == 1
    assert tools[0].name == "get_weather"
    assert tools[0].args == {"city": "SF"}
    assert tools[0].id == "call_1"
