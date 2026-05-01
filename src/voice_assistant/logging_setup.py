"""Logging setup: stdlib logger calls are routed into loguru.

Loguru gives:
- structured JSON sink for ~/.voice-assistant/voice-assistant.log (rotated, 7 days)
- pretty colour sink for the terminal
- per-record context (request_id, user, tool name) when set via loguru.contextualize
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from loguru import logger


class _InterceptHandler(logging.Handler):
    """Forward stdlib logs to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)
        frame = logging.currentframe()
        depth = 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            next_frame = frame.f_back
            if next_frame is None:
                break
            frame = next_frame
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(level: str = "INFO", log_file: Path | str | None = None) -> None:
    """Idempotent: safe to call multiple times. The CLI calls this on startup."""
    # Always reset loguru sinks so re-calls start clean (no duplicate file sinks).
    logger.remove()

    logger.add(
        sys.stderr,
        level=level,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> <level>{level:<7}</level> <cyan>{name}</cyan> | {message}",
    )

    if log_file:
        path = Path(log_file).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            path,
            level=level,  # respect the configured level for file too
            rotation="10 MB",
            retention="7 days",
            serialize=True,  # JSON
            enqueue=False,  # synchronous so test flushes work
        )

    # Install the stdlib→loguru intercept handler.
    # Remove any stale _InterceptHandler instances before adding a new one
    # (handles re-calls within the same process).
    root = logging.getLogger()
    root.handlers = [h for h in root.handlers if not isinstance(h, _InterceptHandler)]
    root.addHandler(_InterceptHandler())
    root.setLevel(logging.DEBUG)  # let loguru handle per-level filtering
