from pathlib import Path
from voice_assistant.safety import SafetyPolicy
from voice_assistant.tools import build_registry


def test_registry_includes_filesystem_tools(sandbox: Path):
    pol = SafetyPolicy(
        allowed_roots=[sandbox],
        destructive_requires_confirmation=True,
        delete_rate_per_minute=5,
    )
    reg = build_registry(policy=pol)
    names = {spec.name for spec in reg}
    assert {
        "create_folder", "create_file", "list_folder",
        "read_file", "move_path", "delete_path",
    }.issubset(names)


def test_registry_invokes_underlying_tool(sandbox: Path):
    pol = SafetyPolicy(
        allowed_roots=[sandbox],
        destructive_requires_confirmation=True,
        delete_rate_per_minute=5,
    )
    reg = build_registry(policy=pol)
    create_folder = next(s for s in reg if s.name == "create_folder")
    target = sandbox / "made"
    r = create_folder.func(path=str(target))
    assert r.ok and target.is_dir()
