from __future__ import annotations
import inspect
from functools import partial
from pathlib import Path
from typing import Any, Callable
from voice_assistant.safety import SafetyPolicy
from voice_assistant.tools.schema import ToolSpec
from voice_assistant.tools import filesystem as fs
from voice_assistant.tools import gmail
from voice_assistant.tools import system


def _bind_filesystem_tool(
    fn: Callable[..., ToolResult], *, policy: SafetyPolicy
) -> Callable[..., ToolResult]:
    """Return a callable that injects `policy` and silently drops unknown kwargs."""
    sig = inspect.signature(fn)
    accepted = set(sig.parameters.keys()) - {"policy"}

    def caller(**kwargs: Any) -> ToolResult:
        clean = {k: v for k, v in kwargs.items() if k in accepted}
        return fn(policy=policy, **clean)

    caller.__name__ = fn.__name__
    caller.__doc__ = fn.__doc__
    return caller


def build_registry(
    *,
    policy: SafetyPolicy,
    gmail_credentials_file: Path | None = None,
) -> list[ToolSpec]:
    specs: list[ToolSpec] = [
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
        ToolSpec(
            name="open_url",
            description="Open an http/https URL in the default browser.",
            parameters={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
                "additionalProperties": False,
            },
            func=system.open_url,
        ),
        ToolSpec(
            name="open_app",
            description=(
                "Launch a desktop application by command name "
                "(e.g. 'firefox', 'code', 'gnome-calculator'). "
                "Always requires confirmed=true."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "confirmed": {"type": "boolean"},
                },
                "required": ["name", "confirmed"],
                "additionalProperties": False,
            },
            func=system.open_app,
        ),
    ]

    if gmail_credentials_file is not None:
        specs.append(
            ToolSpec(
                name="send_email",
                description=(
                    "Send a plain-text email via the user's Gmail account. "
                    "Always confirm with the user before calling this."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["to", "subject", "body"],
                    "additionalProperties": False,
                },
                func=partial(
                    gmail.send_email,
                    credentials_file=str(gmail_credentials_file),
                ),
            )
        )

    try:
        from voice_assistant.tools.web import (
            web_search, web_fetch, WEB_SEARCH_SCHEMA, WEB_FETCH_SCHEMA,
        )
        if web_search is not None and WEB_SEARCH_SCHEMA is not None:
            specs.append(
                ToolSpec(
                    name="web_search",
                    description=WEB_SEARCH_SCHEMA["function"]["description"],
                    parameters=WEB_SEARCH_SCHEMA["function"]["parameters"],
                    func=lambda **kw: _wrap_web_result(web_search(**kw)),
                )
            )
        if web_fetch is not None and WEB_FETCH_SCHEMA is not None:
            specs.append(
                ToolSpec(
                    name="web_fetch",
                    description=WEB_FETCH_SCHEMA["function"]["description"],
                    parameters=WEB_FETCH_SCHEMA["function"]["parameters"],
                    func=lambda **kw: _wrap_web_result(web_fetch(**kw)),
                )
            )
    except ImportError:
        pass  # [web] extra not installed — silently skip

    return specs


def _wrap_web_result(result: object) -> "ToolResult":  # type: ignore[name-defined]  # noqa: F821
    """Wrap a web tool result (list or dict) into a ToolResult."""
    import json
    from voice_assistant.tools.schema import ToolResult
    if isinstance(result, (list, dict)):
        text = json.dumps(result, ensure_ascii=False)
    else:
        text = str(result)
    return ToolResult(ok=True, summary=text[:200])
