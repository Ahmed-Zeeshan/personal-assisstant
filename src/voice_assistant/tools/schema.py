from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
from pydantic import BaseModel


class ToolResult(BaseModel):
    ok: bool
    summary: str
    error: str | None = None
    data: dict[str, Any] | None = None


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]   # JSON schema
    func: Callable[..., ToolResult]

    def to_openai_format(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
