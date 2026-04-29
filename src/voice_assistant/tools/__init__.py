from __future__ import annotations
from functools import partial
from voice_assistant.safety import SafetyPolicy
from voice_assistant.tools.schema import ToolSpec
from voice_assistant.tools import filesystem as fs


def build_registry(*, policy: SafetyPolicy) -> list[ToolSpec]:
    return [
        ToolSpec(
            name="create_folder",
            description="Create a folder (and any missing parents) at `path`.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            func=partial(fs.create_folder, policy=policy),
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
            },
            func=partial(fs.create_file, policy=policy),
        ),
        ToolSpec(
            name="list_folder",
            description="List the entries in the folder at `path`.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            func=partial(fs.list_folder, policy=policy),
        ),
        ToolSpec(
            name="read_file",
            description="Read a text file at `path`. Returns content (capped).",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_bytes": {"type": "integer", "default": 64000},
                },
                "required": ["path"],
            },
            func=partial(fs.read_file, policy=policy),
        ),
        ToolSpec(
            name="move_path",
            description=(
                "Move or rename a file or folder from `src` to `dst`. "
                "If `dst` already exists, set `confirmed=true` to overwrite."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "src": {"type": "string"},
                    "dst": {"type": "string"},
                    "confirmed": {"type": "boolean", "default": False},
                },
                "required": ["src", "dst"],
            },
            func=partial(fs.move_path, policy=policy),
        ),
        ToolSpec(
            name="delete_path",
            description=(
                "Delete a file or folder at `path`. "
                "Always requires `confirmed=true`."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "confirmed": {"type": "boolean", "default": False},
                },
                "required": ["path", "confirmed"],
            },
            func=partial(fs.delete_path, policy=policy),
        ),
    ]
