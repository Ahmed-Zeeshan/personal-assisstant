import os
import time
from pathlib import Path
import pytest
from voice_assistant.safety import SafetyPolicy, SafetyError


def make_policy(roots: list, rate: int = 5, requires_confirmation: bool = True) -> SafetyPolicy:
    return SafetyPolicy(
        allowed_roots=[Path(r) for r in roots],
        destructive_requires_confirmation=requires_confirmation,
        delete_rate_per_minute=rate,
    )


def test_check_path_inside_allowed_root_passes(sandbox: Path):
    pol = make_policy([sandbox])
    pol.check_path(sandbox / "subdir" / "file.txt")


def test_check_path_outside_allowed_root_fails(sandbox: Path):
    pol = make_policy([sandbox])
    with pytest.raises(SafetyError):
        pol.check_path(Path("/etc/passwd"))


def test_check_path_blocks_dotdot_traversal(sandbox: Path):
    pol = make_policy([sandbox])
    with pytest.raises(SafetyError):
        pol.check_path(sandbox / ".." / "outside.txt")


def test_check_path_blocks_symlink_escape(sandbox: Path):
    """A symlink inside the sandbox pointing outside MUST be rejected."""
    target_outside = sandbox.parent / "outside_target"
    target_outside.mkdir()
    link = sandbox / "evil_link"
    link.symlink_to(target_outside)
    pol = make_policy([sandbox])
    with pytest.raises(SafetyError):
        pol.check_path(link / "secret.txt")


def test_check_path_blocks_prefix_confusion(sandbox: Path):
    """A sibling directory whose name shares a prefix with the sandbox must not pass."""
    sibling = sandbox.parent / (sandbox.name + "-evil")
    sibling.mkdir()
    pol = make_policy([sandbox])
    with pytest.raises(SafetyError):
        pol.check_path(sibling / "file.txt")


def test_check_path_rejects_null_byte_path_as_safety_error(sandbox: Path):
    """Malformed input must surface as SafetyError, not raw ValueError."""
    pol = make_policy([sandbox])
    with pytest.raises(SafetyError):
        pol.check_path("foo\x00bar")


def test_destructive_requires_confirmation_flag(sandbox: Path):
    pol = make_policy([sandbox])
    with pytest.raises(SafetyError):
        pol.check_destructive(sandbox / "f", confirmed=False)
    pol.check_destructive(sandbox / "f", confirmed=True)


def test_destructive_rejects_out_of_sandbox_even_when_confirmed(sandbox: Path):
    """confirmed=True must NOT bypass path scoping."""
    pol = make_policy([sandbox])
    with pytest.raises(SafetyError):
        pol.check_destructive(Path("/etc/passwd"), confirmed=True)


def test_destructive_no_confirmation_required_mode(sandbox: Path):
    pol = make_policy([sandbox], requires_confirmation=False)
    pol.check_destructive(sandbox / "f", confirmed=False)  # no exception


def test_allowed_roots_is_immutable(sandbox: Path):
    pol = make_policy([sandbox])
    with pytest.raises((AttributeError, TypeError)):
        pol.allowed_roots.append(Path("/"))  # tuple has no append


def test_allowed_roots_property_cannot_be_replaced(sandbox: Path):
    pol = make_policy([sandbox])
    with pytest.raises(AttributeError):
        pol.allowed_roots = (Path("/"),)


def test_negative_rate_rejected_at_construction(sandbox: Path):
    with pytest.raises(ValueError):
        SafetyPolicy(
            allowed_roots=[sandbox],
            destructive_requires_confirmation=True,
            delete_rate_per_minute=-1,
        )


def test_zero_rate_blocks_all_deletes(sandbox: Path):
    pol = make_policy([sandbox], rate=0)
    with pytest.raises(SafetyError):
        pol.record_delete()


def test_delete_rate_limit(sandbox: Path):
    pol = make_policy([sandbox], rate=2)
    pol.record_delete()
    pol.record_delete()
    with pytest.raises(SafetyError):
        pol.record_delete()


def test_delete_rate_limit_window_resets(sandbox: Path, monkeypatch):
    pol = make_policy([sandbox], rate=2)
    base = time.monotonic()
    monkeypatch.setattr("voice_assistant.safety.time.monotonic", lambda: base)
    pol.record_delete()
    pol.record_delete()
    monkeypatch.setattr("voice_assistant.safety.time.monotonic", lambda: base + 61)
    pol.record_delete()  # window has rolled over
