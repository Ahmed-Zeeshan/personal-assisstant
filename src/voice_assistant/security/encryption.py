"""End-to-end encryption for sensitive user data files.

Key derivation strategy (in order):
  1. OS keychain via ``keyring`` (Linux: Secret Service / KWallet;
     macOS: Keychain; Windows: Credential Manager).
  2. Key file ``~/.voice-assistant/.master.key`` (mode 0600) when keyring is
     unavailable (CI / headless sessions).

Opt-in: encryption is disabled by default.  Set
``security.encrypt_user_data = true`` in ``config.yaml`` to enable it.

CHANGELOG note: encryption applies to *new* writes only — existing plaintext
files are not migrated automatically.
"""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_KEYRING_SERVICE = "voice-assistant"
_KEYRING_USERNAME = "master-key"
_KEY_FILE = Path("~/.voice-assistant/.master.key").expanduser()


# ---------------------------------------------------------------------------
# MasterKey
# ---------------------------------------------------------------------------


class MasterKey:
    """Get-or-create and store the 32-byte Fernet master key."""

    def __init__(self, key_file: Path = _KEY_FILE) -> None:
        self._key_file = key_file
        self._key: bytes | None = None

    # -- public ---------------------------------------------------------------

    def get(self) -> bytes:
        """Return the raw 32-byte key, loading/creating it on first call."""
        if self._key is not None:
            return self._key
        self._key = self._load() or self._create()
        return self._key

    # -- private helpers ------------------------------------------------------

    def _load(self) -> bytes | None:
        """Try keyring then key-file. Return raw bytes or None."""
        # 1. keyring
        raw = self._keyring_get()
        if raw is not None:
            return raw
        # 2. key file
        if self._key_file.exists():
            data = self._key_file.read_bytes().strip()
            if len(data) == 32:
                return data
            # stored as hex (64 chars)
            if len(data) == 64:
                try:
                    return bytes.fromhex(data.decode())
                except ValueError:
                    pass
            log.warning(
                "Encryption key file %s has unexpected length; regenerating", self._key_file
            )
        return None

    def _create(self) -> bytes:
        """Generate a new key and persist it via keyring → key-file."""
        key = os.urandom(32)
        if not self._keyring_set(key):
            self._write_key_file(key)
        return key

    def _keyring_get(self) -> bytes | None:
        try:
            import keyring  # type: ignore[import-untyped,unused-ignore]

            val = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
            if val is not None:
                return bytes.fromhex(str(val))
        except Exception as exc:
            log.debug("keyring unavailable for read: %s", exc)
        return None

    def _keyring_set(self, key: bytes) -> bool:
        try:
            import keyring  # type: ignore[import-untyped,unused-ignore]

            keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, key.hex())
            return True
        except Exception as exc:
            log.debug("keyring unavailable for write (%s); using key file", exc)
            return False

    def _write_key_file(self, key: bytes) -> None:
        self._key_file.parent.mkdir(parents=True, exist_ok=True)
        self._key_file.write_bytes(key.hex().encode())
        self._key_file.chmod(0o600)
        log.info("Wrote new master key to %s", self._key_file)


# Module-level singleton (lazy-initialised on first access)
_master_key = MasterKey()


def _fernet(key: bytes | None = None) -> Any:
    """Return a Fernet instance bound to *key* (or the master key)."""
    from cryptography.fernet import Fernet

    raw = key if key is not None else _master_key.get()
    # Fernet requires a 32-byte URL-safe-base64 key.
    import base64

    fernet_key = base64.urlsafe_b64encode(raw)
    return Fernet(fernet_key)


# ---------------------------------------------------------------------------
# Low-level byte API
# ---------------------------------------------------------------------------


def encrypt_bytes(data: bytes, *, key: bytes | None = None) -> bytes:
    """Encrypt *data* and return the Fernet token (bytes)."""
    return bytes(_fernet(key).encrypt(data))


def decrypt_bytes(blob: bytes, *, key: bytes | None = None) -> bytes:
    """Decrypt a Fernet *blob* and return the original bytes.

    Raises ``cryptography.fernet.InvalidToken`` on any tampering / wrong key.
    """
    from cryptography.fernet import InvalidToken

    try:
        return bytes(_fernet(key).decrypt(blob))
    except Exception as exc:
        raise InvalidToken("Decryption failed — wrong key or corrupt data") from exc


# ---------------------------------------------------------------------------
# File-level helpers
# ---------------------------------------------------------------------------


def encrypt_file(path: Path, *, key: bytes | None = None) -> None:
    """Encrypt *path* in-place.  Preserves the file's permission bits."""
    orig_mode = _get_mode(path)
    blob = encrypt_bytes(path.read_bytes(), key=key)
    path.write_bytes(blob)
    if orig_mode is not None:
        path.chmod(orig_mode)


def decrypt_file(path: Path, *, key: bytes | None = None) -> None:
    """Decrypt *path* in-place.  Preserves the file's permission bits."""
    orig_mode = _get_mode(path)
    data = decrypt_bytes(path.read_bytes(), key=key)
    path.write_bytes(data)
    if orig_mode is not None:
        path.chmod(orig_mode)


def _get_mode(path: Path) -> int | None:
    try:
        return stat.S_IMODE(path.stat().st_mode)
    except OSError:
        return None
