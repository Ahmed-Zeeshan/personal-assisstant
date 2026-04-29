from __future__ import annotations
import copy
from dataclasses import dataclass
from typing import Any, Callable
from pydantic import BaseModel, ConfigDict, model_validator


class ToolResult(BaseModel):
    """Standard return type for every tool.

    `ok=False` always pairs with a non-None `error`.
    """

    model_config = ConfigDict(extra="forbid")

    ok: bool
    summary: str
    error: str | None = None
    data: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _check_error_on_failure(self) -> "ToolResult":
        if not self.ok and self.error is None:
            raise ValueError("error must be set when ok is False")
        return self


@dataclass(frozen=True)
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
                "parameters": copy.deepcopy(self.parameters),
            },
        }
