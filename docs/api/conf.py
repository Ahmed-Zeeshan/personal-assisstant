"""Sphinx configuration for voice-assistant API reference."""
from __future__ import annotations

import sys
from pathlib import Path

# Make the source package importable without installing.
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

# -- Project information -----------------------------------------------------
project = "voice-assistant"
author = "Zeeshan Ahmed"
release = "0.1.0"
copyright = "2026, Zeeshan Ahmed"  # noqa: A001

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

templates_path: list[str] = ["_templates"]
exclude_patterns: list[str] = ["_build", "Thumbs.db", ".DS_Store"]

# autodoc settings
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# Suppress nitpick warnings for third-party and internal types that have no
# Sphinx inventory or are TypeVar-derived.
nitpick_ignore = [
    ("py:class", "Path"),
    ("py:class", "pathlib.Path"),
    ("py:class", "pydantic.main.BaseModel"),
    ("py:class", "collections.abc.Iterator"),
    ("py:class", "collections.abc.Callable"),
    ("py:class", "abc.ABC"),
    ("py:class", "EmbedFn"),
    ("py:class", "voice_assistant.retry.F"),
    ("py:class", "voice_assistant.audio_types.AudioBuffer"),
    # malformed autodoc cross-ref from tools/filesystem.py docstring
    ('py:class', '{"ok"'),
]
nitpick_ignore_regex = []

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path: list[str] = []
