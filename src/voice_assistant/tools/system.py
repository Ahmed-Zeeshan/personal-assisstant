from __future__ import annotations
import shlex
import subprocess
import webbrowser
from voice_assistant.tools.schema import ToolResult


def open_url(url: str) -> ToolResult:
    """Open a URL in the user's default browser. Only http/https allowed."""
    if not (url.startswith("http://") or url.startswith("https://")):
        return ToolResult(
            ok=False, summary="bad url",
            error="only http/https URLs are allowed",
        )
    ok = webbrowser.open(url)
    return ToolResult(
        ok=bool(ok),
        summary=f"opened {url}" if ok else f"failed to open {url}",
        error=None if ok else f"failed to open {url}",
    )


def open_app(name: str) -> ToolResult:
    """Launch a desktop application by command name (e.g. 'firefox')."""
    try:
        cmd = shlex.split(name)
        proc = subprocess.Popen(cmd)
        return ToolResult(ok=True, summary=f"launched {name} (pid={proc.pid})")
    except FileNotFoundError:
        return ToolResult(
            ok=False, summary="app not found", error=f"no such command: {name}"
        )
    except Exception as e:
        return ToolResult(ok=False, summary="launch failed", error=str(e))
