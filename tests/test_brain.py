from unittest.mock import MagicMock

from voice_assistant.brain import (
    Brain,
    Message,
    PlainText,
    ToolCall,
    _build_system_prompt,
)
from voice_assistant.config import UserConfig
from voice_assistant.tools.schema import ToolResult, ToolSpec


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
    b = Brain(provider="anthropic", model="claude-sonnet-4-6")
    out = b.respond(
        user_text="say hello",
        history=[],
        tools=fake_tool(),
    )
    assert isinstance(out, PlainText)
    assert out.content == "hello back"
    assert called["model"] == "anthropic/claude-sonnet-4-6"
    assert any(t["function"]["name"] == "create_folder" for t in called["tools"])


def test_brain_returns_tool_call(monkeypatch):
    tc = MagicMock()
    tc.id = "call_1"
    tc.function.name = "create_folder"
    tc.function.arguments = '{"path": "/tmp/x"}'
    fake = make_litellm_response(tool_calls=[tc])

    monkeypatch.setattr("voice_assistant.brain.completion", lambda **kw: fake)
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


def test_brain_handles_malformed_tool_call_args_gracefully(monkeypatch):
    tc = MagicMock()
    tc.id = "call_1"
    tc.function.name = "create_folder"
    tc.function.arguments = '{"path": '   # truncated JSON
    fake = make_litellm_response(tool_calls=[tc])
    monkeypatch.setattr("voice_assistant.brain.completion", lambda **kw: fake)

    b = Brain(provider="anthropic", model="claude-sonnet-4-6")
    out = b.respond(user_text="x", history=[], tools=fake_tool())
    assert isinstance(out, PlainText)
    assert "malformed" in out.content


def test_brain_logs_warning_on_multiple_tool_calls(monkeypatch, caplog):
    import logging
    tc1 = MagicMock()
    tc1.id = "c1"
    tc1.function.name = "create_folder"
    tc1.function.arguments = '{"path": "/tmp/a"}'
    tc2 = MagicMock()
    tc2.id = "c2"
    tc2.function.name = "create_folder"
    tc2.function.arguments = '{"path": "/tmp/b"}'
    fake = make_litellm_response(tool_calls=[tc1, tc2])
    monkeypatch.setattr("voice_assistant.brain.completion", lambda **kw: fake)

    b = Brain(provider="anthropic", model="claude-sonnet-4-6")
    with caplog.at_level(logging.WARNING, logger="voice_assistant.brain"):
        out = b.respond(user_text="x", history=[], tools=fake_tool())
    assert isinstance(out, ToolCall)
    assert out.id == "c1"
    assert any("2 tool_calls" in r.message for r in caplog.records)


def test_brain_serialises_assistant_tool_calls_in_history(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "voice_assistant.brain.completion",
        lambda **kw: captured.update(kw) or make_litellm_response(content="done"),
    )
    history = [
        Message(role="user", content="please do X"),
        Message(
            role="assistant",
            content="",
            tool_calls=[{
                "id": "call_1",
                "type": "function",
                "function": {"name": "create_folder", "arguments": '{"path":"/tmp/x"}'},
            }],
        ),
        Message(role="tool", content='{"ok": true, "summary": "made /tmp/x"}',
                tool_call_id="call_1", name="create_folder"),
    ]
    b = Brain(provider="anthropic", model="claude-sonnet-4-6")
    b.respond(user_text="thanks", history=history, tools=fake_tool())

    assistant_msg = next(
        m for m in captured["messages"] if m["role"] == "assistant"
    )
    assert "tool_calls" in assistant_msg
    assert assistant_msg["tool_calls"][0]["id"] == "call_1"

    tool_msg = next(
        m for m in captured["messages"] if m["role"] == "tool"
    )
    assert tool_msg["tool_call_id"] == "call_1"


def test_system_prompt_first_name():
    p = _build_system_prompt(UserConfig(name="Zeeshan Ahmed", address_as="first_name"))
    assert "Zeeshan" in p
    assert "Ahmed" not in p  # first name only


def test_system_prompt_title():
    p = _build_system_prompt(UserConfig(name="Zeeshan", address_as="title", title="Boss"))
    assert "Boss" in p


def test_system_prompt_none():
    p = _build_system_prompt(UserConfig(name=None, address_as="none"))
    # No address line at all — the second line should be the rule about response length
    lines = p.splitlines()
    assert "Address" not in lines[1]


def test_system_prompt_includes_language_rule():
    p = _build_system_prompt(UserConfig(name="Zeeshan", address_as="first_name"))
    assert "language" in p.lower()
