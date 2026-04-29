from __future__ import annotations
import shutil
from pathlib import Path
from voice_assistant.safety import SafetyPolicy, SafetyError
from voice_assistant.tools.schema import ToolResult


def _wrap(fn):
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except SafetyError as e:
            return ToolResult(ok=False, summary="blocked by safety", error=str(e))
        except OSError as e:
            return ToolResult(ok=False, summary="filesystem error", error=str(e))
    inner.__name__ = fn.__name__
    inner.__doc__ = fn.__doc__
    return inner


@_wrap
def create_folder(path: str, *, policy: SafetyPolicy) -> ToolResult:
    """Create a folder, including any missing parent folders."""
    p = Path(path).expanduser()
    policy.check_path(p)
    p.mkdir(parents=True, exist_ok=True)
    return ToolResult(ok=True, summary=f"created folder {p}")


@_wrap
def create_file(path: str, *, policy: SafetyPolicy, content: str = "") -> ToolResult:
    """Create a file with optional text content."""
    p = Path(path).expanduser()
    policy.check_path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return ToolResult(ok=True, summary=f"wrote {len(content)} bytes to {p}")


@_wrap
def list_folder(path: str, *, policy: SafetyPolicy) -> ToolResult:
    """List the entries (names only) in a folder."""
    p = Path(path).expanduser()
    policy.check_path(p)
    if not p.is_dir():
        return ToolResult(ok=False, summary="not a folder", error=str(p))
    entries = sorted([e.name for e in p.iterdir()])
    return ToolResult(
        ok=True,
        summary=f"{len(entries)} entries in {p}",
        data={"entries": entries},
    )


@_wrap
def read_file(
    path: str, *, policy: SafetyPolicy, max_bytes: int = 64_000
) -> ToolResult:
    """Read a text file, truncated to max_bytes."""
    p = Path(path).expanduser()
    policy.check_path(p)
    raw = p.read_bytes()
    truncated = len(raw) > max_bytes
    text = raw[:max_bytes].decode("utf-8", errors="replace")
    return ToolResult(
        ok=True,
        summary=f"read {len(text)} bytes from {p}"
        + (" (truncated)" if truncated else ""),
        data={"content": text, "truncated": truncated},
    )


@_wrap
def move_path(
    src: str, dst: str, *, policy: SafetyPolicy, confirmed: bool = False
) -> ToolResult:
    """Move or rename a file or folder. Requires confirmed=True if dst exists."""
    s = Path(src).expanduser()
    d = Path(dst).expanduser()
    policy.check_path(s)
    if d.exists():
        policy.check_destructive(d, confirmed=confirmed)
    else:
        policy.check_path(d)
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(s), str(d))
    return ToolResult(ok=True, summary=f"moved {s} -> {d}")


@_wrap
def delete_path(
    path: str, *, policy: SafetyPolicy, confirmed: bool = False
) -> ToolResult:
    """Delete a file or folder (recursive). Requires confirmed=True."""
    p = Path(path).expanduser()
    policy.check_destructive(p, confirmed=confirmed)
    policy.record_delete()
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()
    return ToolResult(ok=True, summary=f"deleted {p}")
