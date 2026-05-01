"""Tool that returns the running machine's context: OS, time, locale, etc."""
from __future__ import annotations

import locale as _locale
import platform
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def get_system_info() -> dict[str, Any]:
    """Return basic info about the machine the assistant is running on."""
    try:
        tz_name = datetime.now().astimezone().tzinfo.tzname(None) or "UTC"
    except Exception:
        tz_name = "UTC"
    try:
        loc, _ = _locale.getlocale()
    except Exception:
        loc = None
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "machine_arch": platform.machine(),
        "hostname": socket.gethostname(),
        "user_home": str(Path.home()),
        "current_time_iso": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "timezone": tz_name,
        "locale": loc or "C",
        "python_version": platform.python_version(),
    }


SYSTEM_INFO_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_system_info",
        "description": (
            "Return facts about the host machine (OS, hostname, time, timezone, locale). "
            "Use when the user asks about their computer, current time, where they are, etc."
        ),
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
}


def system_context_block() -> str:
    """One-line system-prompt block summarising the host. Cheap, no I/O."""
    info = get_system_info()
    return (
        f"Host: {info['hostname']} ({info['os']} {info['machine_arch']}). "
        f"Time: {info['current_time_iso']}. Timezone: {info['timezone']}. "
        f"Locale: {info['locale']}. Home: {info['user_home']}."
    )
