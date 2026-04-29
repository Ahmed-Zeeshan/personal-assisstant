from pathlib import Path
from unittest.mock import MagicMock
from voice_assistant.app import Orchestrator
from voice_assistant.brain import PlainText, ToolCall
from voice_assistant.safety import SafetyPolicy
from voice_assistant.tools import build_registry


def make_orchestrator(sandbox: Path, brain: MagicMock) -> Orchestrator:
    policy = SafetyPolicy(
        allowed_roots=[sandbox],
        destructive_requires_confirmation=True,
        delete_rate_per_minute=5,
    )
    return Orchestrator(brain=brain, tools=build_registry(policy=policy))


def test_handle_plain_text(sandbox):
    brain = MagicMock()
    brain.respond.side_effect = [PlainText(content="hi there")]
    orch = make_orchestrator(sandbox, brain)
    reply = orch.handle("hello")
    assert reply == "hi there"


def test_handle_tool_call_executes_and_summarises(sandbox):
    brain = MagicMock()
    target = sandbox / "newdir"
    brain.respond.side_effect = [
        ToolCall(id="c1", name="create_folder", arguments={"path": str(target)}),
        PlainText(content="created the folder"),
    ]
    orch = make_orchestrator(sandbox, brain)
    reply = orch.handle("make a folder called newdir")
    assert target.is_dir()
    assert reply == "created the folder"
    assert brain.respond.call_count == 2


def test_unknown_tool_returns_apology(sandbox):
    brain = MagicMock()
    brain.respond.side_effect = [
        ToolCall(id="c1", name="does_not_exist", arguments={}),
        PlainText(content="sorry, I don't know how to do that"),
    ]
    orch = make_orchestrator(sandbox, brain)
    reply = orch.handle("do the impossible")
    assert "sorry" in reply.lower()


import pytest
import logging


def test_history_state_after_tool_call(sandbox):
    brain = MagicMock()
    target = sandbox / "x"
    brain.respond.side_effect = [
        ToolCall(id="c1", name="create_folder", arguments={"path": str(target)}),
        PlainText(content="ok"),
    ]
    orch = make_orchestrator(sandbox, brain)
    orch.handle("make x")
    roles = [m.role for m in orch.history]
    assert roles == ["user", "assistant", "tool", "assistant"]
    assert orch.history[1].tool_calls is not None
    assert orch.history[1].tool_calls[0]["id"] == "c1"
    assert orch.history[2].tool_call_id == "c1"


def test_tool_raising_unexpected_exception_propagates(sandbox):
    """Orchestrator's narrow except is intentional; CLI catches at the loop level."""
    from voice_assistant.tools.schema import ToolSpec
    from voice_assistant.app import Orchestrator
    brain = MagicMock()

    def buggy_tool(**kwargs):
        raise RuntimeError("kaboom")

    bad_spec = ToolSpec(
        name="buggy",
        description="x",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
        func=buggy_tool,
    )
    brain.respond.side_effect = [
        ToolCall(id="c1", name="buggy", arguments={}),
    ]
    orch = Orchestrator(brain=brain, tools=[bad_spec])
    with pytest.raises(RuntimeError):
        orch.handle("trigger buggy")


def test_followup_tool_call_falls_back_to_summary(sandbox, caplog):
    brain = MagicMock()
    target = sandbox / "x"
    brain.respond.side_effect = [
        ToolCall(id="c1", name="create_folder", arguments={"path": str(target)}),
        ToolCall(id="c2", name="create_folder", arguments={"path": str(target)}),
    ]
    orch = make_orchestrator(sandbox, brain)
    with caplog.at_level(logging.WARNING, logger="voice_assistant.app"):
        reply = orch.handle("make x")
    assert "created folder" in reply
    assert any("tool call" in r.message for r in caplog.records)
