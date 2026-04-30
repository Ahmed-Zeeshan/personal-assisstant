from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any, cast

from voice_assistant.safety import SafetyPolicy
from voice_assistant.tools import filesystem as fs
from voice_assistant.tools import gmail, system
from voice_assistant.tools.schema import ToolResult, ToolSpec


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
            WEB_FETCH_SCHEMA,
            WEB_SEARCH_SCHEMA,
            web_fetch,
            web_search,
        )
        if web_search is not None and WEB_SEARCH_SCHEMA is not None:
            fn_s = cast(dict[str, Any], WEB_SEARCH_SCHEMA.get("function", {}))
            specs.append(
                ToolSpec(
                    name="web_search",
                    description=fn_s["description"],
                    parameters=fn_s["parameters"],
                    func=lambda **kw: _wrap_web_result(web_search(**kw)),
                )
            )
        if web_fetch is not None and WEB_FETCH_SCHEMA is not None:
            fn_f = cast(dict[str, Any], WEB_FETCH_SCHEMA.get("function", {}))
            specs.append(
                ToolSpec(
                    name="web_fetch",
                    description=fn_f["description"],
                    parameters=fn_f["parameters"],
                    func=lambda **kw: _wrap_web_result(web_fetch(**kw)),
                )
            )
    except ImportError:
        pass  # [web] extra not installed — silently skip

    # ---- memory tools (optional; requires [memory] extra + API key) ----------
    try:
        import logging as _logging

        from voice_assistant.memory.store import MemoryStore
        from voice_assistant.memory.tool import (
            RECALL_SCHEMA,
            REMEMBER_SCHEMA,
            make_recall_tool,
            make_remember_tool,
        )

        def _embed_fn(text: str) -> list[float]:
            import litellm as _litellm
            resp = _litellm.embedding(model="text-embedding-3-small", input=[text])
            return resp.data[0]["embedding"]  # type: ignore[no-any-return]

        _memory_home = Path.home() / ".voice-assistant"
        _store = MemoryStore(_memory_home / "memory.db", embed=_embed_fn, dim=1536)
        _remember_fn = make_remember_tool(_store)
        _recall_fn = make_recall_tool(_store)

        def _wrap_dict_tool(fn: Any) -> Any:
            """Wrap a dict-returning tool into a ToolResult-returning callable."""
            def _wrapped(**kwargs: Any) -> ToolResult:
                result = fn(**kwargs)
                import json as _json
                text = _json.dumps(result, ensure_ascii=False)
                return ToolResult(ok=True, summary=text[:200], data=result)
            _wrapped.__name__ = getattr(fn, "__name__", "tool")
            return _wrapped

        rem_schema = cast(dict[str, Any], REMEMBER_SCHEMA.get("function", {}))
        rec_schema = cast(dict[str, Any], RECALL_SCHEMA.get("function", {}))
        specs.append(
            ToolSpec(
                name="remember",
                description=rem_schema["description"],
                parameters=rem_schema["parameters"],
                func=_wrap_dict_tool(_remember_fn),
            )
        )
        specs.append(
            ToolSpec(
                name="recall",
                description=rec_schema["description"],
                parameters=rec_schema["parameters"],
                func=_wrap_dict_tool(_recall_fn),
            )
        )
    except Exception as exc:
        import logging as _logging
        _logging.getLogger(__name__).warning("memory tools disabled: %s", exc)

    # ---- browser tools (optional; requires [browser] extra + playwright install) --
    try:
        from voice_assistant.tools.browser import (
            BROWSER_SCHEMAS,
            browser_click,
            browser_goto,
            browser_keyboard,
            browser_read,
            browser_type,
        )

        _browser_fns: dict[str, Any] = {
            "browser_goto":     browser_goto,
            "browser_click":    browser_click,
            "browser_type":     browser_type,
            "browser_read":     browser_read,
            "browser_keyboard": browser_keyboard,
        }
        for _bschema in BROWSER_SCHEMAS:
            _bfn_info = cast(dict[str, Any], _bschema.get("function", {}))
            _bname = _bfn_info.get("name", "")
            if _bname not in _browser_fns:
                continue
            _braw_fn = _browser_fns[_bname]

            def _wrap_browser_tool(fn: Any) -> Any:
                def _wrapped(**kwargs: Any) -> ToolResult:
                    import json as _json
                    result = fn(**kwargs)
                    text = _json.dumps(result, ensure_ascii=False)
                    return ToolResult(ok=True, summary=text[:200], data=result)
                _wrapped.__name__ = getattr(fn, "__name__", "browser_tool")
                return _wrapped

            specs.append(
                ToolSpec(
                    name=_bname,
                    description=_bfn_info.get("description", ""),
                    parameters=_bfn_info.get("parameters", {}),
                    func=_wrap_browser_tool(_braw_fn),
                )
            )
    except ImportError:
        pass  # [browser] extra not installed — silently skip

    # ---- whatsapp tool (optional; requires [browser] extra + playwright install) --
    try:
        from voice_assistant.tools.whatsapp import WHATSAPP_SCHEMA
        from voice_assistant.tools.whatsapp import send_whatsapp_message as _wa_fn

        def _wrap_wa_tool(fn: Any) -> Any:
            def _wrapped(**kwargs: Any) -> ToolResult:
                import json as _json

                result = fn(**kwargs)
                text = _json.dumps(result, ensure_ascii=False)
                return ToolResult(ok=True, summary=text[:200], data=result)

            _wrapped.__name__ = getattr(fn, "__name__", "whatsapp_tool")
            return _wrapped

        _wa_info = cast(dict[str, Any], WHATSAPP_SCHEMA.get("function", {}))
        specs.append(
            ToolSpec(
                name="send_whatsapp_message",
                description=_wa_info.get("description", ""),
                parameters=_wa_info.get("parameters", {}),
                func=_wrap_wa_tool(_wa_fn),
            )
        )
    except ImportError:
        pass  # [browser] extra not installed — silently skip

    return specs


def _wrap_web_result(result: object) -> ToolResult:
    """Wrap a web tool result (list or dict) into a ToolResult."""
    import json

    from voice_assistant.tools.schema import ToolResult
    if isinstance(result, (list, dict)):
        text = json.dumps(result, ensure_ascii=False)
    else:
        text = str(result)
    return ToolResult(ok=True, summary=text[:200])
