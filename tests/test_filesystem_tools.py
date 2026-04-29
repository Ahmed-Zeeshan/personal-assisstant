from pathlib import Path
import pytest
from voice_assistant.safety import SafetyPolicy, SafetyError
from voice_assistant.tools.filesystem import (
    create_folder, create_file, list_folder, read_file,
    move_path, delete_path,
)


@pytest.fixture
def policy(sandbox: Path) -> SafetyPolicy:
    return SafetyPolicy(
        allowed_roots=[sandbox],
        destructive_requires_confirmation=True,
        delete_rate_per_minute=10,
    )


def test_create_folder(policy, sandbox):
    target = sandbox / "alpha" / "beta"
    r = create_folder(str(target), policy=policy)
    assert r.ok
    assert target.is_dir()


def test_create_folder_outside_root_blocked(policy):
    r = create_folder("/etc/voice-assistant-test", policy=policy)
    assert not r.ok and "outside allowed" in (r.error or "")


def test_create_file_with_content(policy, sandbox):
    f = sandbox / "hello.txt"
    r = create_file(str(f), content="hi", policy=policy)
    assert r.ok and f.read_text() == "hi"


def test_list_folder(policy, sandbox):
    (sandbox / "a.txt").write_text("a")
    (sandbox / "b").mkdir()
    r = list_folder(str(sandbox), policy=policy)
    assert r.ok
    names = sorted(r.data["entries"])
    assert names == ["a.txt", "b"]


def test_read_file_size_capped(policy, sandbox):
    f = sandbox / "big.txt"
    f.write_text("x" * (200_000))
    r = read_file(str(f), policy=policy, max_bytes=1024)
    assert r.ok
    assert len(r.data["content"]) == 1024
    assert r.data["truncated"] is True


def test_move_path(policy, sandbox):
    src = sandbox / "from.txt"
    src.write_text("hi")
    dst = sandbox / "to.txt"
    r = move_path(str(src), str(dst), policy=policy, confirmed=True)
    assert r.ok
    assert dst.exists() and not src.exists()


def test_delete_path_requires_confirmation(policy, sandbox):
    f = sandbox / "x.txt"
    f.write_text("x")
    r = delete_path(str(f), policy=policy, confirmed=False)
    assert not r.ok and "confirmed" in (r.error or "")
    assert f.exists()


def test_delete_path_with_confirmation(policy, sandbox):
    f = sandbox / "x.txt"
    f.write_text("x")
    r = delete_path(str(f), policy=policy, confirmed=True)
    assert r.ok
    assert not f.exists()


def test_delete_folder_recursive(policy, sandbox):
    d = sandbox / "tree"
    (d / "inner").mkdir(parents=True)
    (d / "inner" / "f.txt").write_text("hi")
    r = delete_path(str(d), policy=policy, confirmed=True)
    assert r.ok
    assert not d.exists()
