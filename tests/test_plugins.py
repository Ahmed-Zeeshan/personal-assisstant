"""Tests for the MCP/local plugin loader (Item 30)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from voice_assistant.plugins import _load_one, load_plugins

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_policy() -> Any:
    return MagicMock()


def _make_registry() -> list[Any]:
    return []


def _write_plugin(tmp_path: Path, name: str, code: str) -> Path:
    p = tmp_path / name
    p.write_text(code)
    return p


# ---------------------------------------------------------------------------
# _load_one tests
# ---------------------------------------------------------------------------


class TestLoadOne:
    def test_valid_plugin_registers_tool(self, tmp_path: Path) -> None:
        plugin = _write_plugin(
            tmp_path,
            "weather.py",
            """
from voice_assistant.tools.schema import ToolResult, ToolSpec

def register(registry, policy):
    def weather(*, city: str) -> ToolResult:
        return ToolResult(ok=True, summary=f"Weather in {city}: sunny")

    registry.append(ToolSpec(
        name="weather",
        description="Get weather for a city.",
        parameters={
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        },
        func=weather,
    ))
""",
        )
        registry = _make_registry()
        _load_one(plugin, registry, _make_policy())
        assert len(registry) == 1
        assert registry[0].name == "weather"

    def test_plugin_without_register_skipped(self, tmp_path: Path) -> None:
        plugin = _write_plugin(tmp_path, "no_register.py", "x = 42\n")
        registry = _make_registry()
        _load_one(plugin, registry, _make_policy())
        assert len(registry) == 0

    def test_plugin_with_syntax_error_skipped(self, tmp_path: Path) -> None:
        plugin = _write_plugin(tmp_path, "broken.py", "def register(\n  # missing close\n")
        registry = _make_registry()
        _load_one(plugin, registry, _make_policy())
        assert len(registry) == 0

    def test_plugin_register_raises_skipped(self, tmp_path: Path) -> None:
        plugin = _write_plugin(
            tmp_path,
            "raises.py",
            """
def register(registry, policy):
    raise RuntimeError("intentional error")
""",
        )
        registry = _make_registry()
        _load_one(plugin, registry, _make_policy())
        assert len(registry) == 0

    def test_plugin_register_not_callable_skipped(self, tmp_path: Path) -> None:
        plugin = _write_plugin(tmp_path, "not_callable.py", "register = 42\n")
        registry = _make_registry()
        _load_one(plugin, registry, _make_policy())
        assert len(registry) == 0

    def test_plugin_can_register_multiple_tools(self, tmp_path: Path) -> None:
        plugin = _write_plugin(
            tmp_path,
            "multi.py",
            """
from voice_assistant.tools.schema import ToolResult, ToolSpec

def register(registry, policy):
    for name in ["tool_a", "tool_b"]:
        registry.append(ToolSpec(
            name=name,
            description=f"{name} tool",
            parameters={"type": "object", "properties": {}, "additionalProperties": False},
            func=lambda **k: ToolResult(ok=True, summary="ok"),
        ))
""",
        )
        registry = _make_registry()
        _load_one(plugin, registry, _make_policy())
        assert len(registry) == 2
        assert {t.name for t in registry} == {"tool_a", "tool_b"}


# ---------------------------------------------------------------------------
# load_plugins tests
# ---------------------------------------------------------------------------


class TestLoadPlugins:
    def test_no_plugin_dir_is_silent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("voice_assistant.plugins._PLUGIN_DIR", tmp_path / "nonexistent")
        registry = _make_registry()
        load_plugins(registry, _make_policy())  # should not raise
        assert len(registry) == 0

    def test_empty_plugin_dir_is_silent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("voice_assistant.plugins._PLUGIN_DIR", tmp_path)
        registry = _make_registry()
        load_plugins(registry, _make_policy())
        assert len(registry) == 0

    def test_multiple_plugins_all_loaded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("voice_assistant.plugins._PLUGIN_DIR", tmp_path)
        for letter in ["a", "b", "c"]:
            _write_plugin(
                tmp_path,
                f"{letter}.py",
                f"""
from voice_assistant.tools.schema import ToolResult, ToolSpec

def register(registry, policy):
    registry.append(ToolSpec(
        name="tool_{letter}",
        description="Tool {letter}",
        parameters={{"type": "object", "properties": {{}}, "additionalProperties": False}},
        func=lambda **k: ToolResult(ok=True, summary="ok"),
    ))
""".replace("{letter}", letter),
            )
        registry = _make_registry()
        load_plugins(registry, _make_policy())
        assert len(registry) == 3

    def test_broken_plugin_does_not_block_good_plugins(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("voice_assistant.plugins._PLUGIN_DIR", tmp_path)
        # Broken plugin (alphabetically first)
        _write_plugin(
            tmp_path, "aaa_broken.py", "def register(r, p):\n    raise ValueError('oops')\n"
        )
        # Good plugin
        _write_plugin(
            tmp_path,
            "zzz_good.py",
            """
from voice_assistant.tools.schema import ToolResult, ToolSpec

def register(registry, policy):
    registry.append(ToolSpec(
        name="good_tool",
        description="A good tool",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
        func=lambda **k: ToolResult(ok=True, summary="ok"),
    ))
""",
        )
        registry = _make_registry()
        load_plugins(registry, _make_policy())
        # Only the good plugin registers its tool.
        assert len(registry) == 1
        assert registry[0].name == "good_tool"

    def test_tool_func_is_callable_after_load(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("voice_assistant.plugins._PLUGIN_DIR", tmp_path)
        _write_plugin(
            tmp_path,
            "weather.py",
            """
from voice_assistant.tools.schema import ToolResult, ToolSpec

def register(registry, policy):
    def weather(*, city: str) -> ToolResult:
        return ToolResult(ok=True, summary=f"sunny in {city}")

    registry.append(ToolSpec(
        name="weather",
        description="weather",
        parameters={
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        },
        func=weather,
    ))
""",
        )
        registry = _make_registry()
        load_plugins(registry, _make_policy())
        result = registry[0].func(city="London")
        assert result.ok is True
        assert "London" in result.summary
