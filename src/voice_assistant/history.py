"""Append-only JSONL conversation history.

When *encrypt* is True each line is individually Fernet-encrypted (base64
token + newline).  Lines written without encryption and encrypted lines can
NOT be mixed in the same file — encryption is opt-in and applies only to new
files / new deployments.
"""

from __future__ import annotations

import json
import logging
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class History:
    def __init__(self, path: Path, *, encrypt: bool = False) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._encrypt = encrypt

    # ------------------------------------------------------------------
    def append(self, speaker: str, text: str, **extra: Any) -> None:
        rec: dict[str, Any] = {
            "speaker": speaker,
            "text": text,
            "ts": datetime.now(UTC).isoformat(),
            **extra,
        }
        raw = json.dumps(rec)
        if self._encrypt:
            from voice_assistant.security.encryption import encrypt_bytes

            line = encrypt_bytes(raw.encode()).decode() + "\n"
        else:
            line = raw + "\n"
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line)

    def load_recent(self, n: int = 50) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        # Stream the tail without loading the whole file in memory.
        ring: deque[dict[str, Any]] = deque(maxlen=n)
        with self._path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                # Try decryption first (if encrypt mode); fall back to plain JSON.
                if self._encrypt:
                    try:
                        from voice_assistant.security.encryption import decrypt_bytes

                        line = decrypt_bytes(line.encode()).decode()
                    except Exception:  # noqa: BLE001
                        log.debug("skipping undecryptable history line")
                        continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    log.debug("skipping corrupt history line")
                    continue
                ring.append(rec)
        return list(ring)

    def clear(self) -> None:
        if self._path.exists():
            self._path.write_text("")
