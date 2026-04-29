from pathlib import Path
import pytest


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    """Per-test directory the safety layer is allowed to touch."""
    return tmp_path
