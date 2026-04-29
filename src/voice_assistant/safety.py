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
        self.allowed_roots = [Path(r).expanduser().resolve() for r in allowed_roots]
        self.destructive_requires_confirmation = destructive_requires_confirmation
        self.delete_rate_per_minute = delete_rate_per_minute
        self._delete_times: deque[float] = deque()

    def check_path(self, path: Path) -> None:
        resolved = Path(path).expanduser().resolve()
        for root in self.allowed_roots:
            try:
                resolved.relative_to(root)
                return
            except ValueError:
                continue
        raise SafetyError(
            f"path outside allowed roots: {resolved} (allowed: {self.allowed_roots})"
        )

    def check_destructive(self, path: Path, confirmed: bool) -> None:
        self.check_path(path)
        if self.destructive_requires_confirmation and not confirmed:
            raise SafetyError(
                f"destructive op on {path} requires confirmed=True"
            )

    def record_delete(self) -> None:
        now = time.time()
        cutoff = now - 60
        while self._delete_times and self._delete_times[0] < cutoff:
            self._delete_times.popleft()
        if len(self._delete_times) >= self.delete_rate_per_minute:
            raise SafetyError(
                f"delete rate limit exceeded ({self.delete_rate_per_minute}/min)"
            )
        self._delete_times.append(now)
