from pathlib import Path
import time
import pytest
from voice_assistant.safety import SafetyPolicy, SafetyError


def make_policy(roots: list[Path], rate: int = 5) -> SafetyPolicy:
    return SafetyPolicy(
        allowed_roots=[Path(r).resolve() for r in roots],
        destructive_requires_confirmation=True,
        delete_rate_per_minute=rate,
    )


def test_check_path_inside_allowed_root_passes(sandbox: Path):
    pol = make_policy([sandbox])
    pol.check_path(sandbox / "subdir" / "file.txt")  # no exception


def test_check_path_outside_allowed_root_fails(sandbox: Path):
    pol = make_policy([sandbox])
    with pytest.raises(SafetyError):
        pol.check_path(Path("/etc/passwd"))


def test_destructive_requires_confirmation_flag(sandbox: Path):
    pol = make_policy([sandbox])
    with pytest.raises(SafetyError):
        pol.check_destructive(sandbox / "f", confirmed=False)
    pol.check_destructive(sandbox / "f", confirmed=True)


def test_delete_rate_limit(sandbox: Path):
    pol = make_policy([sandbox], rate=2)
    pol.record_delete()
    pol.record_delete()
    with pytest.raises(SafetyError):
        pol.record_delete()


def test_delete_rate_limit_window_resets(sandbox: Path, monkeypatch):
    pol = make_policy([sandbox], rate=2)
    base = time.time()
    monkeypatch.setattr("voice_assistant.safety.time.time", lambda: base)
    pol.record_delete()
    pol.record_delete()
    monkeypatch.setattr("voice_assistant.safety.time.time", lambda: base + 61)
    pol.record_delete()  # window has rolled over
