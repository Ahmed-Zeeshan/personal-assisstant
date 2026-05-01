"""SQLite + sqlite-vec long-term memory store.

Each fact is stored as `(id, text, ts)` with a paired embedding row in a
sqlite-vec virtual table.

Embeddings are produced via a callable supplied at construction so the
store stays unit-testable without network calls.
"""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    import sqlite_vec

    _HAS_VEC = True
except ImportError:
    sqlite_vec = None
    _HAS_VEC = False


EmbedFn = Callable[[str], list[float]]


class MemoryStore:
    def __init__(self, path: Path, *, embed: EmbedFn, dim: int) -> None:
        self._path = path
        self._embed = embed
        self._dim = dim
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        if _HAS_VEC and sqlite_vec is not None:
            try:
                self._conn.enable_load_extension(True)
                sqlite_vec.load(self._conn)
                self._conn.enable_load_extension(False)
            except Exception as exc:
                import logging

                logging.getLogger(__name__).warning("sqlite-vec load failed: %s", exc)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(f"""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                ts REAL NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS facts_vec USING vec0(
                fact_id INTEGER PRIMARY KEY,
                embedding FLOAT[{self._dim}]
            );
        """)
        self._conn.commit()

    def remember(self, text: str) -> int:
        emb = self._embed(text)
        cur = self._conn.execute(
            "INSERT INTO facts(text, ts) VALUES (?, ?)",
            (text, time.time()),
        )
        fact_id = cur.lastrowid
        assert fact_id is not None
        self._conn.execute(
            "INSERT INTO facts_vec(fact_id, embedding) VALUES (?, ?)",
            (fact_id, json.dumps(emb)),
        )
        self._conn.commit()
        return fact_id

    def forget(self, fact_id: int) -> None:
        self._conn.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
        self._conn.execute("DELETE FROM facts_vec WHERE fact_id = ?", (fact_id,))
        self._conn.commit()

    def recall(self, query: str, *, k: int = 3) -> list[dict[str, Any]]:
        emb = self._embed(query)
        rows = self._conn.execute(
            """
            SELECT facts.id, facts.text, facts.ts, distance
            FROM facts_vec
            JOIN facts ON facts.id = facts_vec.fact_id
            WHERE facts_vec.embedding MATCH ?
              AND k = ?
            ORDER BY distance
            """,
            (json.dumps(emb), k),
        ).fetchall()
        return [{"id": r[0], "text": r[1], "ts": r[2], "distance": r[3]} for r in rows]
