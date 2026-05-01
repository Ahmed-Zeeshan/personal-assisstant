"""Tests for the system_info tool."""
from __future__ import annotations

import socket

from voice_assistant.tools.system_info import get_system_info, system_context_block

EXPECTED_KEYS = {
    "os",
    "os_release",
    "os_version",
    "machine_arch",
    "hostname",
    "user_home",
    "current_time_iso",
    "timezone",
    "locale",
    "python_version",
}


def test_get_system_info_returns_expected_keys():
    info = get_system_info()
    assert set(info.keys()) == EXPECTED_KEYS


def test_get_system_info_values_are_strings():
    info = get_system_info()
    for key, val in info.items():
        assert isinstance(val, str), f"key {key!r} should be str, got {type(val)}"
        assert val, f"key {key!r} should not be empty"


def test_get_system_info_hostname_matches_socket():
    info = get_system_info()
    assert info["hostname"] == socket.gethostname()


def test_get_system_info_current_time_is_iso():
    """current_time_iso should contain a date portion like '2026-'."""
    info = get_system_info()
    assert "T" in info["current_time_iso"]  # ISO 8601 separator
    assert len(info["current_time_iso"]) >= 19  # at least YYYY-MM-DDTHH:MM:SS


def test_system_context_block_is_nonempty():
    block = system_context_block()
    assert isinstance(block, str)
    assert len(block) > 10


def test_system_context_block_contains_hostname():
    block = system_context_block()
    hostname = socket.gethostname()
    assert hostname in block


def test_system_context_block_contains_os():
    import platform

    block = system_context_block()
    assert platform.system() in block


def test_system_context_block_contains_time_label():
    block = system_context_block()
    assert "Time:" in block
    assert "Timezone:" in block
