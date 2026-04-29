from __future__ import annotations
import functools
import shutil
from pathlib import Path
from pydantic import ValidationError
from voice_assistant.safety import SafetyPolicy, SafetyError
from voice_assistant.tools.schema import ToolResult


def _wrap(fn):
    """Convert SafetyError, OSError, and ValidationError to ToolResult(ok=False)."""
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except SafetyError as e:
            return ToolResult(ok=False, summary="blocked by safety", error=str(e))
        except OSError as e:
            return ToolResult(ok=False, summary="filesystem error", error=str(e))
        except ValidationError as e:
            return ToolResult(ok=False, summary="bad result construction", error=str(e))
    return inner


@_wrap
def create_folder(path: str, *, policy: SafetyPolicy) -> ToolResult:
    """Create a folder, including any missing parent folders."""
    p = Path(path).expanduser()
    policy.check_path(p)
    p.mkdir(parents=True, exist_ok=True)
    return ToolResult(ok=True, summary=f"created folder {p}")


@_wrap
def create_file(
    path: str, *, policy: SafetyPolicy, content: str = "", confirmed: bool = False
) -> ToolResult:
    """Create a file with optional text content. If the file exists, requires confirmed=True."""
    p = Path(path).expanduser()
    policy.check_path(p)
    if p.exists():
        policy.check_destructive(p, confirmed=confirmed)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    n_bytes = len(content.encode("utf-8"))
    return ToolResult(ok=True, summary=f"wrote {n_bytes} bytes to {p}")


@_wrap
def list_folder(path: str, *, policy: SafetyPolicy) -> ToolResult:
    """List the entries (names only) in a folder."""
    p = Path(path).expanduser()
    policy.check_path(p)
    if not p.is_dir():
        return ToolResult(
            ok=False, summary="not a folder", error=f"not a directory: {p}"
        )
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
    """Read a text file, truncated to max_bytes (operates on a byte budget)."""
    p = Path(path).expanduser()
    policy.check_path(p)
    raw = p.read_bytes()
    truncated = len(raw) > max_bytes
    head = raw[:max_bytes]
    text = head.decode("utf-8", errors="replace")
    return ToolResult(
        ok=True,
        summary=f"read {len(head)} bytes from {p}"
        + (" (truncated)" if truncated else ""),
        data={"content": text, "bytes_read": len(head), "truncated": truncated},
    )


@_wrap
def move_path(
    src: str, dst: str, *, policy: SafetyPolicy, confirmed: bool = False
) -> ToolResult:
    """Move or rename a file/folder. Requires confirmed=True if dst exists or is a directory shutil would merge into."""
    s = Path(src).expanduser()
    d = Path(dst).expanduser()
    policy.check_path(s)
    # If dst is an existing directory, shutil.move places src INSIDE it.
    # Check the resulting final path explicitly so the safety layer covers it.
    final_dst = d / s.name if d.is_dir() else d
    if final_dst.exists():
        policy.check_destructive(final_dst, confirmed=confirmed)
    else:
        policy.check_path(final_dst)
    final_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(s), str(d))
    return ToolResult(ok=True, summary=f"moved {s} -> {final_dst}")


@_wrap
def delete_path(
    path: str, *, policy: SafetyPolicy, confirmed: bool = False
) -> ToolResult:
    """Delete a file or folder (recursive). Always requires confirmed=True.

    The rate-limit slot is consumed only after the existence check passes
    (i.e., when an actual delete attempt occurs). A nonexistent-path call
    does not count against the rate.
    """
    p = Path(path).expanduser()
    policy.check_destructive(p, confirmed=confirmed)
    if not p.exists():
        return ToolResult(ok=False, summary="path does not exist", error=f"does not exist: {p}")
    policy.record_delete()
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()
    return ToolResult(ok=True, summary=f"deleted {p}")
