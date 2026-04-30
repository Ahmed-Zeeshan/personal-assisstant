"""Tool wrappers that expose `remember` and `recall` to the LLM."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from voice_assistant.memory.store import MemoryStore


def make_remember_tool(store: MemoryStore) -> Callable[..., dict[str, Any]]:
    def remember(*, fact: str) -> dict[str, Any]:
        rec_id = store.remember(fact.strip())
        return {"ok": True, "id": rec_id}
    return remember


def make_recall_tool(store: MemoryStore) -> Callable[..., dict[str, Any]]:
    def recall(*, query: str, k: int = 3) -> dict[str, Any]:
        results = store.recall(query, k=max(1, min(int(k), 10)))
        return {"results": [{"text": r["text"], "id": r["id"]} for r in results]}
    return recall


REMEMBER_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "remember",
        "description": (
            "Save a personal fact about the user for later turns. "
            "Use only when the user explicitly asks to remember something or shares a long-lived preference."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "A complete declarative sentence."},
            },
            "required": ["fact"],
            "additionalProperties": False,
        },
    },
}


RECALL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "recall",
        "description": (
            "Search saved personal facts. "
            "Use when the answer depends on something the user told you earlier."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "k":     {"type": "integer", "default": 3},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}
