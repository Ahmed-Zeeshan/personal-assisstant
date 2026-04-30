import logging
from pathlib import Path

from voice_assistant.logging_setup import configure_logging


def test_configure_logging_creates_file_and_level(tmp_path: Path):
    log_file = tmp_path / "app.log"
    configure_logging(level="DEBUG", log_file=log_file)
    log = logging.getLogger("voice_assistant.test")
    log.debug("hello")
    for h in logging.getLogger().handlers:
        if hasattr(h, "flush"):
            h.flush()
    assert log_file.exists()
    assert "hello" in log_file.read_text()


def test_creates_parent_directories(tmp_path: Path):
    nested = tmp_path / "a" / "b" / "c" / "app.log"
    configure_logging(level="INFO", log_file=nested)
    log = logging.getLogger("voice_assistant.test")
    log.info("nested")
    for h in logging.getLogger().handlers:
        if hasattr(h, "flush"):
            h.flush()
    assert nested.exists()


def test_level_filters_messages(tmp_path: Path):
    log_file = tmp_path / "app.log"
    configure_logging(level="WARNING", log_file=log_file)
    log = logging.getLogger("voice_assistant.test")
    log.debug("should-not-appear")
    log.warning("should-appear")
    for h in logging.getLogger().handlers:
        if hasattr(h, "flush"):
            h.flush()
    text = log_file.read_text()
    assert "should-not-appear" not in text
    assert "should-appear" in text


def test_idempotent_no_duplicate_lines(tmp_path: Path):
    log_file = tmp_path / "app.log"
    configure_logging(level="DEBUG", log_file=log_file)
    configure_logging(level="DEBUG", log_file=log_file)
    log = logging.getLogger("voice_assistant.test")
    log.debug("once_unique_sentinel_xyzabc")
    for h in logging.getLogger().handlers:
        if hasattr(h, "flush"):
            h.flush()
    # JSON format: exactly one log line per call (sentinel appears in text + message
    # fields per JSON record — count non-empty lines to detect duplicates).
    lines = [ln for ln in log_file.read_text().splitlines() if ln.strip()]
    assert len(lines) == 1, f"expected 1 log line, got {len(lines)}: {lines}"
