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
