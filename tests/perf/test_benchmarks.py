"""Performance benchmarks using pytest-benchmark (Item 3).

Targets
-------
- Brain._build_system_prompt()      < 1 ms
- History.append() + load_recent()  round-trip
- MemoryStore.recall()              against a 100-item store (mocked embeddings)
- SafetyPolicy.resolve_path()       1 000 random paths

These benchmarks do NOT assert timing thresholds — instead they track
historical results stored as CI artifacts (see .github/workflows/perf.yml).
Regressions become visible over time without blocking the build.

Install:  pip install "voice-assistant[dev]"  (pytest-benchmark is in dev extras)
Run:      pytest tests/perf/ --benchmark-only
"""

from __future__ import annotations

import random
import string
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Skip module gracefully if pytest-benchmark is missing
# ---------------------------------------------------------------------------
pytest.importorskip("pytest_benchmark", reason="pytest-benchmark not installed")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _random_path_segment(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=n))


def _random_subpath(root: Path) -> Path:
    return (
        root / _random_path_segment() / _random_path_segment() / (_random_path_segment() + ".txt")
    )


# ---------------------------------------------------------------------------
# Benchmark: Brain._build_system_prompt
# ---------------------------------------------------------------------------


class TestBrainBuildSystemPrompt:
    def setup_method(self) -> None:
        from voice_assistant.brain import _build_system_prompt

        self._fn = _build_system_prompt

    def test_bench_no_user(self, benchmark: Any) -> None:
        result = benchmark(self._fn, None)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_bench_with_user_first_name(self, benchmark: Any) -> None:
        from voice_assistant.config import UserConfig

        user = UserConfig(name="Alice Wonderland", address_as="first_name", respond_in="auto")
        result = benchmark(self._fn, user)
        assert "Alice" in result

    def test_bench_with_user_full_name(self, benchmark: Any) -> None:
        from voice_assistant.config import UserConfig

        user = UserConfig(name="Alice Wonderland", address_as="full_name", respond_in="auto")
        result = benchmark(self._fn, user)
        assert "Alice Wonderland" in result


# ---------------------------------------------------------------------------
# Benchmark: History.append + load_recent round-trip
# ---------------------------------------------------------------------------


class TestHistoryRoundTrip:
    def test_bench_append_then_load(self, benchmark: Any, tmp_path: Path) -> None:
        from voice_assistant.history import History

        h = History(tmp_path / "history.jsonl")

        def _round_trip() -> list[Any]:
            h.append("user", "benchmark message " + _random_path_segment())
            return h.load_recent(50)

        result = benchmark(_round_trip)
        assert isinstance(result, list)

    def test_bench_load_recent_50_items(self, benchmark: Any, tmp_path: Path) -> None:
        from voice_assistant.history import History

        h = History(tmp_path / "history.jsonl")
        for i in range(200):
            h.append("user" if i % 2 == 0 else "assistant", f"message {i}")

        result = benchmark(h.load_recent, 50)
        assert len(result) == 50


# ---------------------------------------------------------------------------
# Benchmark: MemoryStore.recall with 100 items + mocked embeddings
# ---------------------------------------------------------------------------


class TestMemoryStoreRecall:
    def setup_method(self) -> None:
        pytest.importorskip("sqlite_vec", reason="sqlite-vec not installed")

    def test_bench_recall_100_items(self, benchmark: Any, tmp_path: Path) -> None:
        from voice_assistant.memory.store import MemoryStore

        dim = 8  # tiny dimension for speed

        call_count = 0

        def _embed(text: str) -> list[float]:
            nonlocal call_count
            call_count += 1
            # Deterministic pseudo-random embedding so nearest-neighbour works.
            rng = random.Random(hash(text) & 0xFFFFFFFF)
            return [rng.random() for _ in range(dim)]

        store = MemoryStore(tmp_path / "mem.db", embed=_embed, dim=dim)
        for i in range(100):
            store.remember(f"fact number {i}: the sky is {'blue' if i % 2 == 0 else 'grey'}")

        def _recall() -> list[Any]:
            return store.recall("sky colour", k=3)

        result = benchmark(_recall)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Benchmark: SafetyPolicy.resolve_path on 1 000 random paths
# ---------------------------------------------------------------------------


class TestSafetyPolicyResolvePath:
    def test_bench_check_path_1000_random(self, benchmark: Any, tmp_path: Path) -> None:
        from voice_assistant.safety import SafetyError, SafetyPolicy

        policy = SafetyPolicy(
            allowed_roots=[tmp_path],
            destructive_requires_confirmation=True,
            delete_rate_per_minute=10,
        )
        paths = [_random_subpath(tmp_path) for _ in range(1000)]
        idx = 0

        def _check_one() -> None:
            nonlocal idx
            p = paths[idx % len(paths)]
            idx += 1
            try:
                policy.check_path(p)
            except SafetyError:
                pass

        benchmark(_check_one)

    def test_bench_check_path_outside_root(self, benchmark: Any, tmp_path: Path) -> None:
        """Rejected paths (outside allowed roots) should also be fast."""
        from voice_assistant.safety import SafetyError, SafetyPolicy

        policy = SafetyPolicy(
            allowed_roots=[tmp_path / "allowed"],
            destructive_requires_confirmation=False,
            delete_rate_per_minute=100,
        )
        outside = tmp_path / "other" / "file.txt"

        def _check() -> None:
            try:
                policy.check_path(outside)
            except SafetyError:
                pass

        benchmark(_check)
