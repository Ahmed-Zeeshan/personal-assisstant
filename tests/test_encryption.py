"""Tests for voice_assistant.security.encryption."""
from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path

import pytest

from voice_assistant.security.encryption import (
    MasterKey,
    decrypt_bytes,
    decrypt_file,
    encrypt_bytes,
    encrypt_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fresh_key() -> bytes:
    """Return a fresh random 32-byte key (not the module singleton)."""
    return os.urandom(32)


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------


def test_round_trip_basic() -> None:
    key = _fresh_key()
    plain = b"Hello, voice-assistant!"
    assert decrypt_bytes(encrypt_bytes(plain, key=key), key=key) == plain


def test_round_trip_empty() -> None:
    key = _fresh_key()
    assert decrypt_bytes(encrypt_bytes(b"", key=key), key=key) == b""


def test_round_trip_large(tmp_path: Path) -> None:
    key = _fresh_key()
    plain = os.urandom(1024 * 1024)  # 1 MB
    assert decrypt_bytes(encrypt_bytes(plain, key=key), key=key) == plain


def test_wrong_key_raises() -> None:
    from cryptography.fernet import InvalidToken

    key1 = _fresh_key()
    key2 = _fresh_key()
    blob = encrypt_bytes(b"secret", key=key1)
    with pytest.raises((InvalidToken, Exception)):
        decrypt_bytes(blob, key=key2)


def test_tampered_blob_raises() -> None:
    from cryptography.fernet import InvalidToken

    key = _fresh_key()
    blob = bytearray(encrypt_bytes(b"data", key=key))
    blob[-1] ^= 0xFF  # flip a bit
    with pytest.raises((InvalidToken, Exception)):
        decrypt_bytes(bytes(blob), key=key)


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------


def test_encrypt_file_round_trip(tmp_path: Path) -> None:
    key = _fresh_key()
    f = tmp_path / "sample.txt"
    plain = b"file content 12345"
    f.write_bytes(plain)

    encrypt_file(f, key=key)
    assert f.read_bytes() != plain  # now encrypted

    decrypt_file(f, key=key)
    assert f.read_bytes() == plain


def test_encrypt_file_preserves_mode(tmp_path: Path) -> None:
    key = _fresh_key()
    f = tmp_path / "secret.txt"
    f.write_bytes(b"data")
    f.chmod(0o600)

    encrypt_file(f, key=key)
    mode = stat.S_IMODE(f.stat().st_mode)
    assert mode == 0o600

    decrypt_file(f, key=key)
    mode = stat.S_IMODE(f.stat().st_mode)
    assert mode == 0o600


# ---------------------------------------------------------------------------
# MasterKey — key-file fallback
# ---------------------------------------------------------------------------


def test_master_key_creates_and_reloads(tmp_path: Path) -> None:
    key_file = tmp_path / ".master.key"

    mk1 = MasterKey(key_file=key_file)
    k1 = mk1.get()
    assert len(k1) == 32

    # A second instance reads the same key
    mk2 = MasterKey(key_file=key_file)
    k2 = mk2.get()
    assert k1 == k2


def test_master_key_file_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When keyring is unavailable, master key is written to file at mode 0600."""
    key_file = tmp_path / ".master.key"

    from voice_assistant.security import encryption as enc_mod

    # Make keyring_set always fail so the key-file path is exercised.
    monkeypatch.setattr(MasterKey, "_keyring_set", lambda self, key: False)
    monkeypatch.setattr(MasterKey, "_keyring_get", lambda self: None)

    mk = MasterKey(key_file=key_file)
    mk.get()
    assert key_file.exists(), "Key file should have been created"
    mode = stat.S_IMODE(key_file.stat().st_mode)
    assert mode == 0o600


# ---------------------------------------------------------------------------
# History integration
# ---------------------------------------------------------------------------


def test_history_encrypt_round_trip(tmp_path: Path) -> None:
    """History class writes encrypted lines and reads them back."""
    from voice_assistant.history import History
    from voice_assistant.security import encryption as enc_mod

    # Patch the module-level _master_key so we don't touch the real keychain.
    key = _fresh_key()

    class _FixedKey(MasterKey):
        def get(self) -> bytes:
            return key

    original = enc_mod._master_key
    enc_mod._master_key = _FixedKey()
    try:
        h = History(tmp_path / "history.jsonl", encrypt=True)
        h.append("user", "hello encrypted world")
        raw = (tmp_path / "history.jsonl").read_bytes()
        # Raw file must NOT contain the plaintext
        assert b"hello encrypted world" not in raw

        items = h.load_recent()
        assert len(items) == 1
        assert items[0]["text"] == "hello encrypted world"
    finally:
        enc_mod._master_key = original


def test_history_plain_unaffected(tmp_path: Path) -> None:
    from voice_assistant.history import History

    h = History(tmp_path / "history.jsonl", encrypt=False)
    h.append("user", "plain text entry")
    items = h.load_recent()
    assert items[0]["text"] == "plain text entry"
