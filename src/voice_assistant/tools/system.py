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


def open_app(name: str, *, confirmed: bool = False) -> ToolResult:
    """Launch a desktop application by command name (e.g. 'firefox').

    Always requires confirmed=True. The brain may receive prompt-injected
    instructions from data tools (read_file, etc.) — this guard prevents
    silent execution of arbitrary commands.
    """
    if not confirmed:
        return ToolResult(
            ok=False,
            summary="open_app requires confirmation",
            error="set confirmed=true to launch an application",
        )
    try:
        cmd = shlex.split(name)
        if not cmd:
            return ToolResult(ok=False, summary="empty command", error="empty command")
        proc = subprocess.Popen(cmd)
        return ToolResult(ok=True, summary=f"launched {name} (pid={proc.pid})")
    except FileNotFoundError:
        return ToolResult(
            ok=False, summary="app not found", error=f"no such command: {name}"
        )
    except Exception as e:
        return ToolResult(ok=False, summary="launch failed", error=str(e))
