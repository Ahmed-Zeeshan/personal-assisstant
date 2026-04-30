"""Retry-with-backoff decorator for LLM calls.

Retries only on transient errors (network, rate-limit, timeout). Does NOT
retry on programming bugs (ValueError, TypeError, KeyError) — those should
fail fast.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

log = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def _is_transient(exc: BaseException) -> bool:
    name = type(exc).__name__
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True
    # litellm exceptions are subclasses of openai exceptions in newer versions.
    transient_names = {
        "RateLimitError", "APIConnectionError", "APITimeoutError",
        "ServiceUnavailableError", "InternalServerError", "ReadTimeout",
        "ConnectTimeout", "RemoteProtocolError",
    }
    return name in transient_names


def with_llm_retry(*, max_attempts: int = 3, base_delay: float = 0.5) -> Callable[[F], F]:
    """Retry on transient errors with exponential backoff (0.5, 1.0, 2.0s)."""
    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: BaseException | None = None
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    if not _is_transient(exc):
                        raise
                    last_exc = exc
                    if attempt + 1 == max_attempts:
                        break
                    delay = base_delay * (2 ** attempt)
                    log.warning(
                        "transient error %s in %s; retry %d/%d after %.1fs",
                        type(exc).__name__, fn.__name__,
                        attempt + 1, max_attempts, delay,
                    )
                    time.sleep(delay)
            assert last_exc is not None
            raise last_exc
        return wrapper  # type: ignore[return-value]
    return decorator
