from unittest.mock import MagicMock
import pytest
from voice_assistant.brain import (
    Brain, Message, ToolCall, PlainText, BrainResponse,
)
from voice_assistant.tools.schema import ToolSpec, ToolResult


def fake_tool() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="create_folder",
            description="Create folder",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            func=lambda path: ToolResult(ok=True, summary=f"made {path}"),
        )
    ]


def make_litellm_response(*, content=None, tool_calls=None):
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_brain_returns_plain_text(monkeypatch):
    fake = make_litellm_response(content="hello back")
    called = {}

    def fake_completion(**kwargs):
        called.update(kwargs)
        return fake

    monkeypatch.setattr("voice_assistant.brain.completion", fake_completion)
    b = Brain(provider="claude", model="claude-sonnet-4-6")
    out = b.respond(
        user_text="say hello",
        history=[],
        tools=fake_tool(),
    )
    assert isinstance(out, PlainText)
    assert out.content == "hello back"
    assert called["model"] == "claude/claude-sonnet-4-6"
    assert any(t["function"]["name"] == "create_folder" for t in called["tools"])


def test_brain_returns_tool_call(monkeypatch):
    tc = MagicMock()
    tc.id = "call_1"
    tc.function.name = "create_folder"
    tc.function.arguments = '{"path": "/tmp/x"}'
    fake = make_litellm_response(tool_calls=[tc])

    monkeypatch.setattr(
        "voice_assistant.brain.completion", lambda **kw: fake
    )
    b = Brain(provider="openai", model="gpt-4o")
    out = b.respond(user_text="make /tmp/x", history=[], tools=fake_tool())
    assert isinstance(out, ToolCall)
    assert out.name == "create_folder"
    assert out.arguments == {"path": "/tmp/x"}
    assert out.id == "call_1"


def test_brain_provider_prefix_for_gemini(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "voice_assistant.brain.completion",
        lambda **kw: captured.update(kw) or make_litellm_response(content="ok"),
    )
    b = Brain(provider="gemini", model="gemini-1.5-pro")
    b.respond(user_text="hi", history=[], tools=[])
    assert captured["model"] == "gemini/gemini-1.5-pro"
