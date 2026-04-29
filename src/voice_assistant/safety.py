"""Safety policy: path scoping, destructive-op confirmation, delete rate limit.

This module is the single security gate for filesystem tool calls. Every
tool in `voice_assistant.tools.filesystem` flows through `check_path` or
`check_destructive` before doing I/O.

TOCTOU note: `resolve()` snapshots symlinks at check time. The actual
filesystem syscall (open/unlink/rename) in the tool happens microseconds
later. This window is acceptable for a single-user desktop tool and not
exploitable without local concurrent write access. If this code ever
moves to a multi-user or cloud environment, revisit and either hold an
fd from check time, or use openat()-style relative resolution.
"""
from __future__ import annotations
import time
from collections import deque
from pathlib import Path


class SafetyError(Exception):
    pass


class SafetyPolicy:
    def __init__(
        self,
        allowed_roots: list[Path],
        destructive_requires_confirmation: bool,
        delete_rate_per_minute: int,
    ) -> None:
        if delete_rate_per_minute < 0:
            raise ValueError(
                f"delete_rate_per_minute must be >= 0, got {delete_rate_per_minute}"
            )
        # Stored as a tuple so callers cannot mutate the policy after construction.
        self._allowed_roots: tuple[Path, ...] = tuple(
            Path(r).expanduser().resolve() for r in allowed_roots
        )
        self.destructive_requires_confirmation = destructive_requires_confirmation
        self.delete_rate_per_minute = delete_rate_per_minute
        self._delete_times: deque[float] = deque()

    @property
    def allowed_roots(self) -> tuple[Path, ...]:
        return self._allowed_roots

    def check_path(self, path: Path) -> None:
        try:
            resolved = Path(path).expanduser().resolve()
        except (ValueError, OSError) as exc:
            # null bytes, paths exceeding PATH_MAX, encoding errors, etc.
            raise SafetyError(f"invalid path: {exc}") from exc
        for root in self._allowed_roots:
            try:
                resolved.relative_to(root)
                return
            except ValueError:
                continue
        raise SafetyError(
            f"path outside allowed roots: {resolved}"
        )

    def check_destructive(self, path: Path, confirmed: bool) -> None:
        self.check_path(path)
        if self.destructive_requires_confirmation and not confirmed:
            raise SafetyError(
                f"destructive op on {path} requires confirmed=True"
            )

    def record_delete(self) -> None:
        # Monotonic clock — not affected by NTP adjustments or wall-clock jumps.
        now = time.monotonic()
        cutoff = now - 60
        while self._delete_times and self._delete_times[0] < cutoff:
            self._delete_times.popleft()
        if len(self._delete_times) >= self.delete_rate_per_minute:
            raise SafetyError(
                f"delete rate limit exceeded ({self.delete_rate_per_minute}/min)"
            )
        self._delete_times.append(now)
