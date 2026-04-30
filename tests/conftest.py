import logging
from pathlib import Path

import pytest


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    """Per-test directory the safety layer is allowed to touch."""
    return tmp_path


@pytest.fixture(autouse=True)
def _clean_root_logger_handlers():
    """Restore root logger handlers between tests so logging_setup tests don't leak."""
    root = logging.getLogger()
    saved = list(root.handlers)
    saved_level = root.level
    yield
    for h in list(root.handlers):
        h.close()
        root.removeHandler(h)
    for h in saved:
        root.addHandler(h)
    root.setLevel(saved_level)
