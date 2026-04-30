from pathlib import Path

import pytest

from voice_assistant.safety import SafetyPolicy
from voice_assistant.tools.filesystem import (
    create_file,
    create_folder,
    delete_path,
    list_folder,
    move_path,
    read_file,
)


@pytest.fixture
def policy(sandbox: Path) -> SafetyPolicy:
    return SafetyPolicy(
        allowed_roots=[sandbox],
        destructive_requires_confirmation=True,
        delete_rate_per_minute=10,
    )


# ---------- create_folder ----------

def test_create_folder(policy, sandbox):
    target = sandbox / "alpha" / "beta"
    r = create_folder(str(target), policy=policy)
    assert r.ok
    assert target.is_dir()


def test_create_folder_outside_root_blocked(policy):
    r = create_folder("/etc/voice-assistant-test", policy=policy)
    assert not r.ok and "outside allowed" in (r.error or "")


# ---------- create_file ----------

def test_create_file_with_content(policy, sandbox):
    f = sandbox / "hello.txt"
    r = create_file(str(f), content="hi", policy=policy)
    assert r.ok and f.read_text() == "hi"


def test_create_file_overwrite_requires_confirmation(policy, sandbox):
    f = sandbox / "exists.txt"
    f.write_text("original")
    r = create_file(str(f), content="new", policy=policy, confirmed=False)
    assert not r.ok and "confirmed" in (r.error or "")
    assert f.read_text() == "original"


def test_create_file_overwrite_with_confirmation(policy, sandbox):
    f = sandbox / "exists.txt"
    f.write_text("original")
    r = create_file(str(f), content="new", policy=policy, confirmed=True)
    assert r.ok
    assert f.read_text() == "new"


# ---------- list_folder ----------

def test_list_folder(policy, sandbox):
    (sandbox / "a.txt").write_text("a")
    (sandbox / "b").mkdir()
    r = list_folder(str(sandbox), policy=policy)
    assert r.ok
    names = sorted(r.data["entries"])
    assert names == ["a.txt", "b"]


def test_list_folder_on_file_returns_error(policy, sandbox):
    f = sandbox / "x.txt"
    f.write_text("x")
    r = list_folder(str(f), policy=policy)
    assert not r.ok and "not a directory" in (r.error or "")


# ---------- read_file ----------

def test_read_file_size_capped(policy, sandbox):
    f = sandbox / "big.txt"
    f.write_text("x" * 200_000)
    r = read_file(str(f), policy=policy, max_bytes=1024)
    assert r.ok
    assert r.data["bytes_read"] == 1024
    assert r.data["truncated"] is True


def test_read_file_missing_returns_error(policy, sandbox):
    r = read_file(str(sandbox / "no-such-file.txt"), policy=policy)
    assert not r.ok and r.error


# ---------- move_path ----------

def test_move_path(policy, sandbox):
    src = sandbox / "from.txt"
    src.write_text("hi")
    dst = sandbox / "to.txt"
    r = move_path(str(src), str(dst), policy=policy, confirmed=True)
    assert r.ok
    assert dst.exists() and not src.exists()


def test_move_path_into_existing_directory_checks_final_dst(policy, sandbox):
    src = sandbox / "moveable.txt"
    src.write_text("hi")
    dst_dir = sandbox / "destdir"
    dst_dir.mkdir()
    r = move_path(str(src), str(dst_dir), policy=policy, confirmed=False)
    assert r.ok  # final path doesn't exist yet, so confirmation not required
    assert (dst_dir / "moveable.txt").exists()


def test_move_path_missing_src_returns_error(policy, sandbox):
    r = move_path(
        str(sandbox / "missing.txt"),
        str(sandbox / "dest.txt"),
        policy=policy,
        confirmed=True,
    )
    assert not r.ok and r.error


# ---------- delete_path ----------

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


def test_delete_path_missing_returns_error(policy, sandbox):
    r = delete_path(str(sandbox / "no-such-file.txt"), policy=policy, confirmed=True)
    assert not r.ok and "does not exist" in (r.error or "")


def test_delete_rate_limit_blocks(sandbox):
    pol = SafetyPolicy(
        allowed_roots=[sandbox],
        destructive_requires_confirmation=True,
        delete_rate_per_minute=2,
    )
    for i in range(2):
        f = sandbox / f"f{i}.txt"
        f.write_text("x")
        r = delete_path(str(f), policy=pol, confirmed=True)
        assert r.ok
    f = sandbox / "third.txt"
    f.write_text("x")
    r = delete_path(str(f), policy=pol, confirmed=True)
    assert not r.ok and "rate limit" in (r.error or "")


# ---------- decorator metadata ----------

def test_wrap_preserves_function_metadata():
    assert create_folder.__name__ == "create_folder"
    assert "Create a folder" in (create_folder.__doc__ or "")
    assert hasattr(create_folder, "__wrapped__")
