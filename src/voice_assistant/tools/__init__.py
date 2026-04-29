from __future__ import annotations
import inspect
from typing import Any, Callable
from voice_assistant.safety import SafetyPolicy
from voice_assistant.tools.schema import ToolSpec, ToolResult
from voice_assistant.tools import filesystem as fs


def _bind_filesystem_tool(
    fn: Callable[..., ToolResult], *, policy: SafetyPolicy
) -> Callable[..., ToolResult]:
    """Return a callable that injects `policy` and silently drops unknown kwargs.

    This is defence-in-depth against an LLM emitting unexpected fields. The
    schema's `additionalProperties: false` is the primary guard at the API
    boundary; this binding is the secondary guard at the call site.
    """
    sig = inspect.signature(fn)
    accepted = set(sig.parameters.keys()) - {"policy"}

    def caller(**kwargs: Any) -> ToolResult:
        clean = {k: v for k, v in kwargs.items() if k in accepted}
        return fn(policy=policy, **clean)

    caller.__name__ = fn.__name__
    caller.__doc__ = fn.__doc__
    return caller


def build_registry(*, policy: SafetyPolicy) -> list[ToolSpec]:
    return [
        ToolSpec(
            name="create_folder",
            description="Create a folder (and any missing parents) at `path`.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
            func=_bind_filesystem_tool(fs.create_folder, policy=policy),
        ),
        ToolSpec(
            name="create_file",
            description=(
                "Create a text file at `path` with optional `content`. "
                "If the file already exists, set `confirmed=true` to overwrite."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string", "default": ""},
                    "confirmed": {"type": "boolean", "default": False},
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            func=_bind_filesystem_tool(fs.create_file, policy=policy),
        ),
        ToolSpec(
            name="list_folder",
            description=(
                "List the names of files and subfolders directly inside `path`. "
                "Returns a flat list of entry names (not full paths, no metadata)."
            ),
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
            func=_bind_filesystem_tool(fs.list_folder, policy=policy),
        ),
        ToolSpec(
            name="read_file",
            description=(
                "Read a text file at `path`. Returns content; large files are "
                "capped at `max_bytes` bytes (default 64000)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_bytes": {"type": "integer", "default": 64000},
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            func=_bind_filesystem_tool(fs.read_file, policy=policy),
        ),
        ToolSpec(
            name="move_path",
            description=(
                "Move or rename a file or folder from `src` to `dst`. "
                "If `dst` is an existing directory, `src` is placed inside it. "
                "If the resolved destination path already exists, "
                "set `confirmed=true` to proceed."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "src": {"type": "string"},
                    "dst": {"type": "string"},
                    "confirmed": {"type": "boolean", "default": False},
                },
                "required": ["src", "dst"],
                "additionalProperties": False,
            },
            func=_bind_filesystem_tool(fs.move_path, policy=policy),
        ),
        ToolSpec(
            name="delete_path",
            description=(
                "Delete a file or folder at `path` (recursive for folders). "
                "Always requires `confirmed=true`."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "confirmed": {"type": "boolean"},
                },
                "required": ["path", "confirmed"],
                "additionalProperties": False,
            },
            func=_bind_filesystem_tool(fs.delete_path, policy=policy),
        ),
    ]
