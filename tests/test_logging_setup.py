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
