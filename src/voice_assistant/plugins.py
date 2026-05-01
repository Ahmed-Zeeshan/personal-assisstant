"""Plugin loader for voice-assistant.

Two plugin modes are planned:

Mode 1 — Local Python plugins (SHIPPED IN THIS RELEASE)
    Drop a ``*.py`` file into ``~/.voice-assistant/plugins/``.  Each file must
    expose a ``register(registry, policy)`` function::

        def register(registry: list, policy) -> None:
            from voice_assistant.tools.schema import ToolResult, ToolSpec

            def weather(*, city: str) -> ToolResult:
                return ToolResult(ok=True, summary=f"Weather in {city}: sunny, 22 °C")

            registry.append(ToolSpec(
                name="weather",
                description="Get the current weather for a city.",
                parameters={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                    "additionalProperties": False,
                },
                func=weather,
            ))

    Broken plugins are caught and logged; they do NOT crash startup.

Mode 2 — MCP server URLs (FOLLOW-UP — NOT YET IMPLEMENTED)
    List URLs in ``~/.voice-assistant/plugins.yaml`` under a ``mcp_servers``
    key.  The loader will connect via the Model Context Protocol and pull the
    remote tool list.

    TODO: Implement MCP client (stdio/SSE transport).  The specification is at
          https://spec.modelcontextprotocol.io/  The client should call
          ``tools/list`` on startup and wrap each result as a ``ToolSpec``.
"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass  # TYPE_CHECKING block reserved for future type-only imports

log = logging.getLogger(__name__)

_PLUGIN_DIR = Path.home() / ".voice-assistant" / "plugins"


def load_plugins(registry: list[Any], policy: Any) -> None:
    """Walk ``~/.voice-assistant/plugins/*.py`` and call ``register()`` on each.

    Parameters
    ----------
    registry:
        Mutable list of :class:`~voice_assistant.tools.schema.ToolSpec` objects.
        Each plugin's ``register()`` appends to this list in-place.
    policy:
        The active :class:`~voice_assistant.safety.SafetyPolicy`.  Passed
        through to plugins so they can perform path-scoped operations safely.
    """
    if not _PLUGIN_DIR.exists():
        log.debug("plugin directory %s does not exist — skipping plugin load", _PLUGIN_DIR)
        return

    plugin_files = sorted(_PLUGIN_DIR.glob("*.py"))
    if not plugin_files:
        log.debug("no plugins found in %s", _PLUGIN_DIR)
        return

    log.info("loading %d plugin(s) from %s", len(plugin_files), _PLUGIN_DIR)
    for plugin_path in plugin_files:
        _load_one(plugin_path, registry, policy)

    # TODO (Mode 2): Also load MCP server tools from
    # ~/.voice-assistant/plugins.yaml (mcp_servers list).
    # See module docstring for the planned interface.


def _load_one(path: Path, registry: list[Any], policy: Any) -> None:
    """Import a single plugin file and call its ``register()`` function."""
    module_name = f"va_plugin_{path.stem}"
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            log.warning("plugin %s: could not create module spec — skipping", path.name)
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception:
        log.exception("plugin %s: import failed — skipping", path.name)
        return

    register_fn = getattr(module, "register", None)
    if register_fn is None:
        log.warning("plugin %s: no 'register' function — skipping", path.name)
        return
    if not callable(register_fn):
        log.warning("plugin %s: 'register' is not callable — skipping", path.name)
        return

    before = len(registry)
    try:
        register_fn(registry, policy)
    except Exception:
        log.exception("plugin %s: register() raised — skipping", path.name)
        return

    added = len(registry) - before
    log.info("plugin %s: registered %d tool(s)", path.name, added)
