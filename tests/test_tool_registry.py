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
        "create_folder",
        "create_file",
        "list_folder",
        "read_file",
        "move_path",
        "delete_path",
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


def test_registry_drops_unknown_kwargs(sandbox: Path):
    pol = SafetyPolicy(
        allowed_roots=[sandbox],
        destructive_requires_confirmation=True,
        delete_rate_per_minute=5,
    )
    reg = build_registry(policy=pol)
    create_folder = next(s for s in reg if s.name == "create_folder")
    target = sandbox / "made"
    # extra `policy` and other unknown kwargs are dropped, not forwarded
    r = create_folder.func(path=str(target), policy="evil", surprise="boo")
    assert r.ok and target.is_dir()


def test_registry_schemas_have_additional_properties_false(sandbox: Path):
    pol = SafetyPolicy(
        allowed_roots=[sandbox],
        destructive_requires_confirmation=True,
        delete_rate_per_minute=5,
    )
    reg = build_registry(policy=pol)
    for spec in reg:
        assert spec.parameters.get("additionalProperties") is False, (
            f"{spec.name} schema missing additionalProperties: false"
        )


def test_delete_path_schema_has_no_default_for_confirmed(sandbox: Path):
    pol = SafetyPolicy(
        allowed_roots=[sandbox],
        destructive_requires_confirmation=True,
        delete_rate_per_minute=5,
    )
    reg = build_registry(policy=pol)
    delete = next(s for s in reg if s.name == "delete_path")
    confirmed_schema = delete.parameters["properties"]["confirmed"]
    assert "default" not in confirmed_schema
    assert "confirmed" in delete.parameters["required"]


def test_registry_includes_send_email_when_credentials_present(sandbox: Path, tmp_path):
    from unittest.mock import MagicMock, patch

    pol = SafetyPolicy(
        allowed_roots=[sandbox],
        destructive_requires_confirmation=True,
        delete_rate_per_minute=5,
    )
    creds = tmp_path / "creds.json"
    creds.write_text("{}")
    reg = build_registry(policy=pol, gmail_credentials_file=creds)
    names = {spec.name for spec in reg}
    assert "send_email" in names

    send = next(s for s in reg if s.name == "send_email")
    fake_service = MagicMock()
    fake_send = fake_service.users.return_value.messages.return_value.send
    fake_send.return_value.execute.return_value = {"id": "xyz"}
    with patch("voice_assistant.tools.gmail._build_service", return_value=fake_service):
        r = send.func(to="alice@example.com", subject="hi", body="hi")
    assert r.ok
