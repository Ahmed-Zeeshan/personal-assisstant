import numpy as np

from voice_assistant.memory.store import MemoryStore


def _fake_embed(text: str) -> list[float]:
    """Deterministic hash → 8-dim embedding for tests."""
    rng = np.random.default_rng(seed=hash(text) & 0xFFFFFFFF)
    return rng.random(8).tolist()


def test_remember_and_recall_returns_top_match(tmp_path):
    store = MemoryStore(tmp_path / "memory.db", embed=_fake_embed, dim=8)
    store.remember("My wife's name is Hadia.")
    store.remember("I drive a 2020 Honda Civic.")
    results = store.recall("What's my wife called?", k=1)
    assert len(results) == 1
    assert "Hadia" in results[0]["text"]


def test_recall_empty_when_no_facts(tmp_path):
    store = MemoryStore(tmp_path / "memory.db", embed=_fake_embed, dim=8)
    assert store.recall("anything", k=3) == []


def test_remember_returns_id(tmp_path):
    store = MemoryStore(tmp_path / "memory.db", embed=_fake_embed, dim=8)
    rec_id = store.remember("Foo")
    assert isinstance(rec_id, int)
    assert rec_id > 0


def test_forget_removes_fact(tmp_path):
    store = MemoryStore(tmp_path / "memory.db", embed=_fake_embed, dim=8)
    rec_id = store.remember("My favourite color is purple.")
    store.forget(rec_id)
    results = store.recall("color", k=5)
    assert all("purple" not in r["text"] for r in results)
