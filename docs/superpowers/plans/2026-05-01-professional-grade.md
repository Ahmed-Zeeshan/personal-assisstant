# Professional-grade upgrade — combined design & plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Twelve coordinated improvements to lift the project to production-grade and add the killer capability the user wants (WhatsApp messaging via browser automation):

1. **CI pipeline** — GitHub Actions: ruff + mypy strict + pytest + npm build + Lighthouse
2. **ruff** for lint + format
3. **mypy strict** on `src/`
4. **Pre-commit hooks** (ruff, gitleaks)
5. **Dependabot + pip-audit** weekly scan
6. **Retry-with-backoff** on all LLM calls
7. **Structured logging** (loguru — JSON to file, pretty to terminal)
8. **Browser automation tool** (Playwright + persistent profile)
9. **`send_whatsapp` tool** — built on Playwright, with rate limit
10. **Long-term memory** — sqlite + sqlite-vec
11. **Conversation history** — `~/.voice-assistant/history.jsonl` persistence
12. **GUI keyboard shortcuts** (`Cmd/Ctrl+K`, `/`, `Esc`, `Cmd+,`)

**Architecture:**
- New optional extras in `pyproject.toml`: `dev` (extended), `browser` (Playwright + greenlet), `memory` (sqlite-vec + numpy already pulled).
- All async-required tools (Playwright) run in a dedicated thread with their own asyncio loop, exposed via sync facades to the orchestrator.
- The retry decorator wraps `Brain.complete` and `Brain.complete_stream` — backoff on `litellm.RateLimitError`, `httpx.ConnectError`, `httpx.ReadTimeout`. Max 3 attempts.
- loguru replaces the stdlib logger ONLY at the application boundary (cli.py); library modules continue using `logging.getLogger(__name__)` so they remain importable without loguru. A small `logging_setup.configure_logging` shim routes stdlib logs into loguru when loguru is installed.
- Browser tool reuses Playwright's persistent context API. Profile lives at `~/.voice-assistant/browser-profile/`. Per-tool methods take a unique step ID so the LLM can chain multi-step actions.
- WhatsApp tool composes browser primitives. Hard-coded selectors (with timeouts and clear error messages so the LLM can self-correct).
- Memory: SQLite db at `~/.voice-assistant/memory.db`. Two tables: `facts(id, text, embedding BLOB, created_at)` and `episodes(id, role, content, ts)`. Embeddings via litellm's embedding API (model from config, defaults to `text-embedding-3-small` for openai, `voyage-3` for anthropic — but for MVP, just use `text-embedding-3-small` regardless of brain provider since OpenAI's embedding API is small/cheap and accepted via litellm).
- History: `~/.voice-assistant/history.jsonl`, append-only. GUI's transcript shows last 50 lines on open. New `clear history` menu item.
- Keyboard shortcuts: vanilla DOM `keydown` listener in `web/src/main.ts`.

**Tech Stack:** ruff · mypy · GitHub Actions · pre-commit · gitleaks · pip-audit · tenacity · loguru · playwright · sqlite-vec · trafilatura (already there) · TypeScript.

---

## File Structure

**Created:**
- `.github/workflows/ci.yml` — full CI matrix
- `.github/workflows/audit.yml` — weekly dependency scan
- `.github/dependabot.yml` — automated upgrade PRs
- `.pre-commit-config.yaml`
- `pyproject.toml` (modified) — add `[tool.ruff]`, `[tool.mypy]`, new extras
- `mypy.ini` if `pyproject.toml` config doesn't take it
- `src/voice_assistant/retry.py` — `with_retry` decorator
- `src/voice_assistant/logging_setup.py` (modify) — loguru integration
- `src/voice_assistant/history.py` — JSONL append + load_recent
- `src/voice_assistant/memory/__init__.py`
- `src/voice_assistant/memory/store.py` — sqlite + sqlite-vec wrapper
- `src/voice_assistant/memory/tool.py` — `remember`, `recall` tools
- `src/voice_assistant/tools/browser.py` — Playwright browser tool
- `src/voice_assistant/tools/whatsapp.py` — `send_whatsapp_message`
- `tests/test_retry.py`
- `tests/test_history.py`
- `tests/test_memory_store.py`
- `tests/test_browser_tool.py`
- `tests/test_whatsapp_tool.py`

**Modified:**
- `src/voice_assistant/brain.py` — wrap `complete` and `complete_stream` with retry
- `src/voice_assistant/tools/__init__.py` — register new tools (browser, whatsapp, remember, recall) when their extras are installed
- `src/voice_assistant/app.py` — append every turn to history; auto-recall relevant memories before brain call
- `src/voice_assistant/cli.py` — wire history loading on GUI start; expose history.jsonl path
- `src/voice_assistant/desktop/bridge.py` — emit history on `pywebviewready`
- `web/src/types.ts` — add `history_replay` event
- `web/src/components/Transcript.ts` — `replayHistory(items)` method
- `web/src/main.ts` — keyboard shortcuts + history replay handler
- `scripts/install.sh` / `install.ps1` — install browser binaries (`python -m playwright install chromium`)

---

## Task 1: ruff + mypy strict + pre-commit + dependabot

**Files:**
- Create: `.github/dependabot.yml`
- Create: `.pre-commit-config.yaml`
- Create: `mypy.ini` (or `[tool.mypy]` in `pyproject.toml`)
- Modify: `pyproject.toml` (add `[tool.ruff]`)

- [ ] **Step 1: Add `[tool.ruff]` to `pyproject.toml`**

```toml
[tool.ruff]
target-version = "py311"
line-length = 100
extend-exclude = ["src/voice_assistant/desktop/web_dist"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP", "S", "N", "RUF"]
ignore = [
  "E501",   # line too long (formatter handles it)
  "S101",   # assert allowed (we use it in tests + dev)
  "S603",   # subprocess call risk — we use it for legitimate tools
  "S607",   # subprocess partial path — same
  "B008",   # function call in argument default (FastAPI/typer pattern, used in tests)
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S", "N802", "B011"]
```

- [ ] **Step 2: Add `[tool.mypy]` to `pyproject.toml`**

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_unreachable = true
warn_redundant_casts = true
warn_unused_ignores = true
exclude = [
  "^tests/",
  "^build/",
  "^src/voice_assistant/desktop/web_dist/",
]

# Pragmatic: third-party libs without good stubs
[[tool.mypy.overrides]]
module = ["litellm.*", "duckduckgo_search.*", "trafilatura.*", "webview.*", "pyaudio.*", "sounddevice.*", "piper.*", "pynput.*", "playwright.*", "sqlite_vec.*"]
ignore_missing_imports = true
```

- [ ] **Step 3: Create `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
        exclude: '\.md$'
      - id: check-yaml
      - id: check-toml
      - id: check-json
        exclude: 'tsconfig.json|web/.*\.json'   # tsconfig allows comments
```

- [ ] **Step 4: Create `.github/dependabot.yml`**

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
  - package-ecosystem: "npm"
    directory: "/web"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
  - package-ecosystem: "npm"
    directory: "/website"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

- [ ] **Step 5: Run ruff + mypy locally and fix the obvious issues**

```bash
~/.local/share/voice-assistant/.venv/bin/pip install ruff mypy
~/.local/share/voice-assistant/.venv/bin/ruff check src/ tests/ --fix
~/.local/share/voice-assistant/.venv/bin/ruff format src/ tests/
~/.local/share/voice-assistant/.venv/bin/mypy src/voice_assistant
```

mypy will surface real type errors. **Fix only what's needed to make CI green** — don't gold-plate. Common fixes:
- Add `from __future__ import annotations` if missing in any file.
- Replace `Any` with concrete types where the type is obvious.
- Use `Mapping[str, Any]` for input dicts, `dict[str, Any]` for outputs.
- Add `# type: ignore[<error-code>]` *only* on lines where the third-party library is genuinely untyped and there's no clean fix.

- [ ] **Step 6: Run pytest to confirm tests still pass after the lint pass**

```bash
~/.local/share/voice-assistant/.venv/bin/pytest -q
```

- [ ] **Step 7: Commit**

```bash
git add .github/dependabot.yml .pre-commit-config.yaml pyproject.toml src/ tests/
git commit -m "chore(quality): ruff + mypy strict + pre-commit + dependabot"
```

---

## Task 2: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/audit.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[gmail,web]"
          pip install ruff mypy pytest pytest-mock pytest-cov
      - name: Lint
        run: ruff check src/ tests/
      - name: Format check
        run: ruff format --check src/ tests/
      - name: Type check
        run: mypy src/voice_assistant
      - name: Tests
        run: pytest -q --cov=voice_assistant --cov-report=term-missing --cov-fail-under=70

  web-bundle:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: 'web/package-lock.json'
      - name: Install
        run: cd web && npm ci
      - name: Build
        run: cd web && npm run build

  website:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: 'website/package-lock.json'
      - name: Install
        run: cd website && npm ci
      - name: Build
        run: cd website && npm run build
```

(Cov threshold 70 is permissive on purpose — current is around there. Tighten to 80 once the new tests land.)

- [ ] **Step 2: Create `.github/workflows/audit.yml`**

```yaml
name: Security audit

on:
  schedule:
    - cron: "0 6 * * 1"   # Monday 06:00 UTC
  workflow_dispatch:

jobs:
  pip-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install
        run: pip install -e . pip-audit
      - name: Audit
        run: pip-audit --strict --skip-editable

  npm-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: web/
        run: cd web && npm audit --omit=dev --audit-level=high
      - name: website/
        run: cd website && npm audit --omit=dev --audit-level=high
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/
git commit -m "ci: pytest + ruff + mypy + npm builds + weekly audit"
```

(Push deferred to Task 12 so we don't burn Actions minutes on every commit.)

---

## Task 3: Retry-with-backoff for LLM calls

**Files:**
- Create: `src/voice_assistant/retry.py`
- Create: `tests/test_retry.py`
- Modify: `src/voice_assistant/brain.py` (apply decorator)
- Modify: `pyproject.toml` (add `tenacity`)

- [ ] **Step 1: Failing test**

```python
# tests/test_retry.py
import pytest
from voice_assistant.retry import with_llm_retry


def test_retries_on_transient_error_then_succeeds(monkeypatch):
    calls = {"n": 0}

    @with_llm_retry(max_attempts=3)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("transient")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3


def test_gives_up_after_max_attempts():
    @with_llm_retry(max_attempts=2)
    def always_broken():
        raise ConnectionError("nope")
    with pytest.raises(ConnectionError):
        always_broken()


def test_does_not_retry_on_value_error():
    """ValueError is a programming bug, not a transient — don't retry."""
    calls = {"n": 0}

    @with_llm_retry(max_attempts=3)
    def bad():
        calls["n"] += 1
        raise ValueError("bug")

    with pytest.raises(ValueError):
        bad()
    assert calls["n"] == 1
```

- [ ] **Step 2: Implement `retry.py`**

```python
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
from typing import TypeVar, Any

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
```

- [ ] **Step 3: Wrap `Brain.complete` and `Brain.complete_stream`**

In `brain.py`:

```python
from voice_assistant.retry import with_llm_retry

class Brain:
    @with_llm_retry()
    def complete(self, ...):
        ...

    # Streaming retries the whole stream (which yields a generator).
    # Wrapping with_llm_retry means the generator is retried as a whole if
    # litellm raises before yielding anything. After the first yield, errors
    # mid-stream are not retried — they bubble up to the orchestrator.
    @with_llm_retry()
    def _start_stream(self, ...):
        return litellm.completion(..., stream=True)

    def complete_stream(self, ...):
        response = self._start_stream(...)
        # ... existing stream-processing loop ...
```

- [ ] **Step 4: Add `tenacity` is NOT needed; we're using stdlib. But add no extra dependency.**

- [ ] **Step 5: Tests pass**

```bash
~/.local/share/voice-assistant/.venv/bin/pytest tests/test_retry.py tests/test_brain.py tests/test_streaming.py -v
```

- [ ] **Step 6: Commit**

```bash
git add src/voice_assistant/retry.py tests/test_retry.py src/voice_assistant/brain.py
git commit -m "feat(retry): exponential-backoff retries on transient LLM errors"
```

---

## Task 4: Structured logging via loguru

**Files:**
- Modify: `pyproject.toml` (add `loguru` to base deps)
- Modify: `src/voice_assistant/logging_setup.py`

- [ ] **Step 1: Add `loguru` to `[project] dependencies`**

```toml
dependencies = [
    "pyyaml>=6.0",
    "pydantic>=2.5",
    "litellm>=1.80",
    "python-dotenv>=1.0",
    "loguru>=0.7",
]
```

- [ ] **Step 2: Replace `logging_setup.py`**

```python
"""Logging setup: stdlib logger calls are routed into loguru.

Loguru gives:
- structured JSON sink for ~/.voice-assistant/voice-assistant.log (rotated, 7 days)
- pretty colour sink for the terminal
- per-record context (request_id, user, tool name) when set via loguru.contextualize
"""
from __future__ import annotations
import logging
import sys
from pathlib import Path

from loguru import logger


class _InterceptHandler(logging.Handler):
    """Forward stdlib logs to loguru."""
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


_configured = False


def configure_logging(level: str = "INFO", log_file: Path | str | None = None) -> None:
    """Idempotent: safe to call multiple times. The CLI calls this on startup."""
    global _configured
    logger.remove()  # always reset

    logger.add(
        sys.stderr,
        level=level,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> <level>{level:<7}</level> <cyan>{name}</cyan> | {message}",
    )

    if log_file:
        path = Path(log_file).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            path,
            level="DEBUG",
            rotation="10 MB",
            retention="7 days",
            serialize=True,  # JSON
            enqueue=True,    # async-safe across threads
        )

    if not _configured:
        logging.root.handlers = [_InterceptHandler()]
        logging.root.setLevel(level)
        _configured = True
```

- [ ] **Step 3: All call sites already use `logging.getLogger(__name__)` → `log.info(...)`. No changes needed.**

- [ ] **Step 4: Run all tests**

```bash
~/.local/share/voice-assistant/.venv/bin/pip install loguru
~/.local/share/voice-assistant/.venv/bin/pytest -q
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/voice_assistant/logging_setup.py
git commit -m "feat(logging): structured loguru sink (JSON to file, colour to terminal)"
```

---

## Task 5: Conversation history (jsonl)

**Files:**
- Create: `src/voice_assistant/history.py`
- Create: `tests/test_history.py`
- Modify: `src/voice_assistant/cli.py` — call history on every assistant turn
- Modify: `src/voice_assistant/desktop/bridge.py` — emit `history_replay` on init
- Modify: `web/src/types.ts` — add `history_replay` event
- Modify: `web/src/components/Transcript.ts` — `replayHistory(items)`
- Modify: `web/src/main.ts` — handle `history_replay`

- [ ] **Step 1: Failing test**

```python
# tests/test_history.py
import json
from pathlib import Path
from voice_assistant.history import History


def test_append_and_load_recent(tmp_path):
    h = History(tmp_path / "history.jsonl")
    h.append("user", "hello")
    h.append("assistant", "hi there")
    items = h.load_recent(50)
    assert len(items) == 2
    assert items[0]["speaker"] == "user"
    assert items[0]["text"] == "hello"
    assert items[1]["speaker"] == "assistant"
    assert items[1]["text"] == "hi there"


def test_load_recent_caps_count(tmp_path):
    h = History(tmp_path / "history.jsonl")
    for i in range(100):
        h.append("user", f"msg-{i}")
    items = h.load_recent(50)
    assert len(items) == 50
    # Last 50, oldest first
    assert items[0]["text"] == "msg-50"
    assert items[-1]["text"] == "msg-99"


def test_clear(tmp_path):
    h = History(tmp_path / "history.jsonl")
    h.append("user", "hello")
    h.clear()
    assert h.load_recent(50) == []


def test_corrupt_lines_are_skipped(tmp_path):
    p = tmp_path / "history.jsonl"
    p.write_text('{"speaker":"user","text":"good","ts":"2026-05-01T00:00:00Z"}\n{not json}\n{"speaker":"assistant","text":"also good","ts":"2026-05-01T00:00:01Z"}\n')
    h = History(p)
    items = h.load_recent(50)
    assert len(items) == 2
    assert items[0]["text"] == "good"
    assert items[1]["text"] == "also good"
```

- [ ] **Step 2: Implement `history.py`**

```python
"""Append-only JSONL conversation history."""
from __future__ import annotations
import json
import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class History:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, speaker: str, text: str, **extra: Any) -> None:
        rec = {
            "speaker": speaker,
            "text": text,
            "ts": datetime.now(timezone.utc).isoformat(),
            **extra,
        }
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    def load_recent(self, n: int = 50) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        # Stream the tail without loading the whole file in memory.
        ring: deque[dict[str, Any]] = deque(maxlen=n)
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
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
```

- [ ] **Step 3: Tests pass**

```bash
~/.local/share/voice-assistant/.venv/bin/pytest tests/test_history.py -v
```

- [ ] **Step 4: Wire into `cli.py` (`_run_gui_mode`)**

Inside `_run_gui_mode`, near the top:

```python
from voice_assistant.history import History
history = History(home / "history.jsonl")
```

In `_do_request`, replace the `bus.publish({"type": "transcript", "speaker": "user", ...})` line with:

```python
history.append("user", text)
bus.publish({"type": "transcript", "speaker": "user", "text": text})
```

After the streaming loop completes (in the `done` branch and at the end of `_do_request`), append the assistant reply:

```python
elif ev["type"] == "done":
    history.append("assistant", buf)
    bus.publish({"type": "transcript_end"})
```

- [ ] **Step 5: Bridge emits history on init**

In `bridge.py`, add a constructor parameter `history: History | None = None` and a getter exposed to JS:

```python
def get_history(self) -> list[dict[str, Any]]:
    if self._history is None:
        return []
    return self._history.load_recent(50)
```

Pass it from `cli.py`:

```python
bridge = Bridge(..., history=history, ...)
```

- [ ] **Step 6: Update `web/src/types.ts`**

```ts
export type HistoryItem = { speaker: 'user'|'assistant'; text: string; ts?: string };

export type VAEvent =
  | ...existing...
  | { type: 'history_replay'; items: HistoryItem[] };
```

- [ ] **Step 7: Add `replayHistory` to `Transcript.ts`**

```ts
replayHistory(items: HistoryItem[]): void {
  if (items.length === 0) return;
  if (this.el.querySelector('p.text-dim')) this.el.replaceChildren();
  for (const item of items) {
    this.push({ speaker: item.speaker, text: item.text });
  }
}
```

(Reuse `push` so we don't duplicate rendering logic.)

- [ ] **Step 8: Update `web/src/bridge.ts` to expose `getHistory()` and call it on init**

```ts
// In bridge.ts:
declare global {
  interface Window {
    pywebview: {
      api: {
        ...existing methods...
        get_history(): Promise<HistoryItem[]>;
      };
    };
  }
}

export const bridge = {
  ...existing...
  getHistory: async (): Promise<HistoryItem[]> => hasPy()
    ? window.pywebview.api.get_history()
    : [],
};

// In the ready handler:
document.addEventListener('pywebviewready', () => {
  void bridge.getConfig().then((cfg) => bus.emit({ type: 'config', cfg }));
  void bridge.getHistory().then((items) => bus.emit({ type: 'history_replay', items }));
});
```

- [ ] **Step 9: Update `web/src/main.ts` to handle `history_replay`**

```ts
case 'history_replay':
  transcript.replayHistory(e.items);
  break;
```

- [ ] **Step 10: Build, test**

```bash
cd web && npm run build
cd /home/zeeshan-ahmed/voice-assistant && ~/.local/share/voice-assistant/.venv/bin/pytest -q
```

- [ ] **Step 11: Commit**

```bash
git add src/voice_assistant/history.py tests/test_history.py src/voice_assistant/cli.py src/voice_assistant/desktop/bridge.py web/src/types.ts web/src/components/Transcript.ts web/src/bridge.ts web/src/main.ts src/voice_assistant/desktop/web_dist/
git commit -m "feat(history): persistent conversation history (~/.voice-assistant/history.jsonl)"
```

---

## Task 6: Long-term memory (sqlite + sqlite-vec)

**Files:**
- Modify: `pyproject.toml` (add `memory` extra)
- Create: `src/voice_assistant/memory/__init__.py`
- Create: `src/voice_assistant/memory/store.py`
- Create: `src/voice_assistant/memory/tool.py`
- Create: `tests/test_memory_store.py`
- Modify: `src/voice_assistant/tools/__init__.py`

- [ ] **Step 1: Add `memory` extra to `pyproject.toml`**

```toml
memory = [
    "sqlite-vec>=0.1.6",
    "numpy>=1.26",     # already in audio extra; pin here too for clarity
]
```

- [ ] **Step 2: Failing test**

```python
# tests/test_memory_store.py
import numpy as np
from pathlib import Path
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
```

- [ ] **Step 3: Implement `memory/store.py`**

```python
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
    import sqlite_vec  # type: ignore
except ImportError:
    sqlite_vec = None


EmbedFn = Callable[[str], list[float]]


class MemoryStore:
    def __init__(self, path: Path, *, embed: EmbedFn, dim: int) -> None:
        self._path = path
        self._embed = embed
        self._dim = dim
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        if sqlite_vec is not None:
            self._conn.enable_load_extension(True)
            sqlite_vec.load(self._conn)
            self._conn.enable_load_extension(False)
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
            f"""
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
```

- [ ] **Step 4: Implement `memory/tool.py`**

```python
"""Tool wrappers that expose `remember` and `recall` to the LLM."""
from __future__ import annotations
from typing import Any
from voice_assistant.memory.store import MemoryStore


def make_remember_tool(store: MemoryStore):
    def remember(*, fact: str) -> dict[str, Any]:
        rec_id = store.remember(fact.strip())
        return {"ok": True, "id": rec_id}
    return remember


def make_recall_tool(store: MemoryStore):
    def recall(*, query: str, k: int = 3) -> dict[str, Any]:
        results = store.recall(query, k=max(1, min(int(k), 10)))
        return {"results": [{"text": r["text"], "id": r["id"]} for r in results]}
    return recall


REMEMBER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "remember",
        "description": "Save a personal fact about the user for later turns. Use only when the user explicitly asks to remember something or shares a long-lived preference.",
        "parameters": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "A complete declarative sentence."},
            },
            "required": ["fact"],
            "additionalProperties": False,
        },
    },
}


RECALL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "recall",
        "description": "Search saved personal facts. Use when the answer depends on something the user told you earlier.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "k":     {"type": "integer", "default": 3},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}
```

- [ ] **Step 5: Wire into `tools/__init__.py`**

In `build_registry`:

```python
try:
    from voice_assistant.memory.store import MemoryStore
    from voice_assistant.memory.tool import (
        make_remember_tool, make_recall_tool, REMEMBER_SCHEMA, RECALL_SCHEMA,
    )
    import litellm

    def _embed(text: str) -> list[float]:
        resp = litellm.embedding(model="text-embedding-3-small", input=[text])
        return resp.data[0]["embedding"]

    home = Path.home() / ".voice-assistant"
    store = MemoryStore(home / "memory.db", embed=_embed, dim=1536)
    registry.register("remember", make_remember_tool(store), REMEMBER_SCHEMA)
    registry.register("recall",   make_recall_tool(store),   RECALL_SCHEMA)
except (ImportError, Exception) as exc:
    log.warning("memory tools disabled: %s", exc)
```

(Match the actual `register` API. If embeddings fail at import time because there's no API key, the tools still register but `recall` will fail at call time — that's acceptable; the LLM can route around it.)

- [ ] **Step 6: Tests pass**

```bash
~/.local/share/voice-assistant/.venv/bin/pip install sqlite-vec
~/.local/share/voice-assistant/.venv/bin/pytest tests/test_memory_store.py -v
```

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml src/voice_assistant/memory/ src/voice_assistant/tools/__init__.py tests/test_memory_store.py
git commit -m "feat(memory): sqlite-vec long-term memory with remember/recall tools"
```

---

## Task 7: Browser automation tool (Playwright)

**Files:**
- Modify: `pyproject.toml` (add `browser` extra)
- Create: `src/voice_assistant/tools/browser.py`
- Create: `tests/test_browser_tool.py`
- Modify: `src/voice_assistant/tools/__init__.py`

- [ ] **Step 1: Add `browser` extra**

```toml
browser = [
    "playwright>=1.49",
]
```

After install, run: `playwright install chromium`. The install scripts must do this — see Task 11.

- [ ] **Step 2: Implement `tools/browser.py`** (single-context manager that exposes sync methods)

```python
"""Browser automation tool — Playwright with a persistent profile.

The first call launches Chromium with a profile dir at
~/.voice-assistant/browser-profile/. Subsequent calls reuse it (so logins
persist).

Public API is sync; Playwright's async loop is hidden behind a worker
thread + asyncio.run_coroutine_threadsafe.
"""
from __future__ import annotations
import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

log = logging.getLogger(__name__)


class _BrowserSession:
    """Singleton-ish: one persistent Chromium per process."""
    _lock = threading.Lock()
    _instance: "_BrowserSession | None" = None

    def __init__(self, profile_dir: Path, headless: bool) -> None:
        self._profile = profile_dir
        self._headless = headless
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._context = None  # playwright BrowserContext
        self._ready = threading.Event()
        self._start_thread()

    def _start_thread(self) -> None:
        def run() -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._setup())
            self._ready.set()
            self._loop.run_forever()
        self._thread = threading.Thread(target=run, name="va-browser", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=30)

    async def _setup(self) -> None:
        from playwright.async_api import async_playwright  # type: ignore
        self._profile.mkdir(parents=True, exist_ok=True)
        self._pw = await async_playwright().start()
        self._context = await self._pw.chromium.launch_persistent_context(
            user_data_dir=str(self._profile),
            headless=self._headless,
            viewport={"width": 1280, "height": 800},
        )

    def _run(self, coro):
        assert self._loop is not None
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=60)

    @classmethod
    def get(cls, *, profile_dir: Path, headless: bool = False) -> "_BrowserSession":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(profile_dir, headless)
            return cls._instance

    async def _page(self):
        assert self._context is not None
        if self._context.pages:
            return self._context.pages[-1]
        return await self._context.new_page()

    # ---- public sync facade ---------------------------------------------------
    def goto(self, url: str) -> dict:
        async def _go():
            page = await self._page()
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            return {"url": page.url, "title": await page.title()}
        return self._run(_go())

    def click(self, selector: str) -> dict:
        async def _click():
            page = await self._page()
            await page.click(selector, timeout=10000)
            return {"ok": True}
        return self._run(_click())

    def type_text(self, selector: str, text: str) -> dict:
        async def _type():
            page = await self._page()
            await page.fill(selector, text, timeout=10000)
            return {"ok": True}
        return self._run(_type())

    def read(self, selector: str = "body") -> dict:
        async def _read():
            page = await self._page()
            text = await page.inner_text(selector, timeout=10000)
            return {"text": text[:8000]}
        return self._run(_read())

    def screenshot(self, *, path: Path) -> dict:
        async def _shot():
            page = await self._page()
            await page.screenshot(path=str(path), type="png")
            return {"path": str(path)}
        return self._run(_shot())

    def keyboard_press(self, key: str) -> dict:
        async def _press():
            page = await self._page()
            await page.keyboard.press(key)
            return {"ok": True}
        return self._run(_press())

    def wait_for(self, selector: str, *, timeout_ms: int = 10000) -> dict:
        async def _wait():
            page = await self._page()
            await page.wait_for_selector(selector, timeout=timeout_ms)
            return {"ok": True}
        return self._run(_wait())


def _session(profile_dir: Path | None = None) -> _BrowserSession:
    return _BrowserSession.get(
        profile_dir=profile_dir or Path.home() / ".voice-assistant" / "browser-profile",
    )


# ---- tool functions exposed to the LLM -----------------------------------------

def browser_goto(*, url: str) -> dict:
    return _session().goto(url)


def browser_click(*, selector: str) -> dict:
    return _session().click(selector)


def browser_type(*, selector: str, text: str) -> dict:
    return _session().type_text(selector, text)


def browser_read(*, selector: str = "body") -> dict:
    return _session().read(selector)


def browser_keyboard(*, key: str) -> dict:
    return _session().keyboard_press(key)


# Schemas omitted for brevity — copy the pattern from tools/web.py.
# Names: browser_goto / browser_click / browser_type / browser_read / browser_keyboard.
```

- [ ] **Step 3: Tests** — see plan source for the full test file with mocked `_BrowserSession`. Skipped here for length; pattern is `monkeypatch.setattr(...)` over the singleton.

- [ ] **Step 4: Register in `tools/__init__.py`** — same pattern as web tools.

- [ ] **Step 5: Install browser binaries**

```bash
~/.local/share/voice-assistant/.venv/bin/pip install playwright
~/.local/share/voice-assistant/.venv/bin/playwright install chromium
```

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/voice_assistant/tools/browser.py tests/test_browser_tool.py src/voice_assistant/tools/__init__.py
git commit -m "feat(tools): Playwright browser automation with persistent profile"
```

---

## Task 8: WhatsApp send tool

**Files:**
- Create: `src/voice_assistant/tools/whatsapp.py`
- Create: `tests/test_whatsapp_tool.py`
- Modify: `src/voice_assistant/tools/__init__.py`

- [ ] **Step 1: Implement `tools/whatsapp.py`**

```python
"""WhatsApp send tool. Built on the Playwright browser tool.

First call: WhatsApp Web loads, you scan a QR code from the phone (one-time).
Subsequent calls: fully automatic.

Hard rate limit: 5 messages / 5 minutes — prevents accidental spam that
WhatsApp's anti-automation could ban the number for.
"""
from __future__ import annotations
import re
import time
from collections import deque
from urllib.parse import quote
from typing import Any
from voice_assistant.tools.browser import _session


_RATE_LIMIT_WINDOW_S = 300
_RATE_LIMIT_COUNT = 5
_recent_sends: deque[float] = deque()


def _check_rate_limit() -> None:
    now = time.time()
    while _recent_sends and _recent_sends[0] < now - _RATE_LIMIT_WINDOW_S:
        _recent_sends.popleft()
    if len(_recent_sends) >= _RATE_LIMIT_COUNT:
        raise RuntimeError(
            f"WhatsApp rate limit hit: max {_RATE_LIMIT_COUNT} messages "
            f"per {_RATE_LIMIT_WINDOW_S // 60} minutes. Wait and retry."
        )


def _normalize_phone(phone: str) -> str:
    """Accept '+44 7700 900000' or '447700900000' or '07700900000'.
    Returns the digits only; the URL handler doesn't need '+'."""
    digits = re.sub(r"\D", "", phone)
    if not digits:
        raise ValueError(f"phone has no digits: {phone!r}")
    return digits


def send_whatsapp_message(*, phone: str, message: str) -> dict[str, Any]:
    """Send a WhatsApp message to a phone number via WhatsApp Web.

    Args:
        phone: International phone number with country code. Examples:
               '+923001234567', '923001234567', '00923001234567'.
        message: The message text. Max ~1000 chars (WhatsApp's limit).

    Returns:
        {"ok": True, "phone": <normalized>} on success.

    Raises:
        RuntimeError: if rate-limited, or WhatsApp Web isn't logged in.
        ValueError: invalid phone or empty message.
    """
    if not message.strip():
        raise ValueError("message cannot be empty")
    if len(message) > 1000:
        raise ValueError("WhatsApp messages capped at ~1000 characters")
    digits = _normalize_phone(phone)
    _check_rate_limit()

    sess = _session()

    # Step 1: open the chat. wa.me redirects to web.whatsapp.com/send/?phone=…&text=…
    url = f"https://web.whatsapp.com/send?phone={digits}&text={quote(message)}"
    sess.goto(url)

    # Step 2: wait for the chat to load — WhatsApp Web shows a "Continue to Chat" button
    # the first time, otherwise it goes straight to the message composer.
    # We wait for the send button (data-testid="send" or aria-label="Send").
    try:
        sess.wait_for('[data-testid="send"], button[aria-label="Send"], span[data-icon="send"]', timeout_ms=30000)
    except Exception as exc:
        raise RuntimeError(
            "WhatsApp Web didn't load the chat. Likely cause: not logged in. "
            "Run send_whatsapp_message once interactively to scan the QR code."
        ) from exc

    # Step 3: click send (multiple selectors as a fallback because WhatsApp's DOM changes).
    for sel in ('[data-testid="send"]', 'button[aria-label="Send"]', 'span[data-icon="send"]'):
        try:
            sess.click(sel)
            _recent_sends.append(time.time())
            return {"ok": True, "phone": digits}
        except Exception:
            continue

    # Last-ditch: hit Enter in the composer
    try:
        sess.keyboard_press("Enter")
        _recent_sends.append(time.time())
        return {"ok": True, "phone": digits, "via": "enter-key"}
    except Exception as exc:
        raise RuntimeError(f"failed to click send button: {exc}") from exc


WHATSAPP_SCHEMA = {
    "type": "function",
    "function": {
        "name": "send_whatsapp_message",
        "description": (
            "Send a WhatsApp message to a phone number via WhatsApp Web. "
            "Phone must include the country code (e.g. +923001234567). "
            "First use requires the user to scan a QR code in the launched browser; "
            "subsequent sends are automatic. Rate-limited to 5/5min to avoid bans."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "phone":   {"type": "string", "description": "Phone number with country code."},
                "message": {"type": "string", "description": "Message text, ≤1000 chars."},
            },
            "required": ["phone", "message"],
            "additionalProperties": False,
        },
    },
}
```

- [ ] **Step 2: Tests** — mock `_session()` to verify the URL composition, rate limit, and the click-fallback chain.

- [ ] **Step 3: Register in `tools/__init__.py`**

- [ ] **Step 4: Commit**

```bash
git add src/voice_assistant/tools/whatsapp.py tests/test_whatsapp_tool.py src/voice_assistant/tools/__init__.py
git commit -m "feat(tools): send_whatsapp_message via WhatsApp Web (Playwright)"
```

---

## Task 9: GUI keyboard shortcuts

**Files:**
- Modify: `web/src/main.ts`

- [ ] **Step 1: Add a global key handler**

In `web/src/main.ts`, after the `bus.on(...)` registration, add:

```ts
document.addEventListener('keydown', (e) => {
  // Ignore typing inside form elements
  const target = e.target as HTMLElement;
  const inForm = target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT');

  // Cmd/Ctrl + , → open settings
  if ((e.metaKey || e.ctrlKey) && e.key === ',') {
    e.preventDefault();
    if (currentConfig) settings.open(currentConfig);
    return;
  }
  // Esc → close settings
  if (e.key === 'Escape') {
    settings.close();
    return;
  }
  if (inForm) return;
  // / → focus composer
  if (e.key === '/') {
    e.preventDefault();
    composerInput()?.focus();
    return;
  }
  // Cmd/Ctrl + K → focus composer with hint
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    composerInput()?.focus();
    return;
  }
});

function composerInput(): HTMLInputElement | null {
  return document.querySelector<HTMLInputElement>('footer [data-input]');
}
```

- [ ] **Step 2: Build, smoke**

```bash
cd web && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add web/src/main.ts src/voice_assistant/desktop/web_dist/
git commit -m "feat(desktop): keyboard shortcuts (Cmd/Ctrl+, K Esc /)"
```

---

## Task 10: Install scripts add browser binaries

**Files:**
- Modify: `scripts/install.sh`
- Modify: `scripts/install.ps1`

- [ ] **Step 1: install.sh — after pip install, add**

```bash
# Browser automation binaries (Chromium + deps).
if "$VA_HOME/.venv/bin/python" -c "import playwright" 2>/dev/null; then
  say "installing Chromium for browser automation (~150 MB)"
  if ! "$VA_HOME/.venv/bin/playwright" install chromium 2>&1 | tail -3; then
    warn "playwright chromium install failed — browser/whatsapp tools won't work until: $VA_HOME/.venv/bin/playwright install chromium"
  fi
fi
```

- [ ] **Step 2: install.ps1 — same pattern**

```powershell
$pyHasPW = & $pip show playwright 2>&1 | Select-String "^Name: playwright"
if ($pyHasPW) {
  Say "installing Chromium for browser automation"
  & (Join-Path $VaHome '.venv\Scripts\playwright.exe') install chromium
  if ($LASTEXITCODE -ne 0) {
    Warn "playwright chromium install failed; browser/whatsapp tools won't work until you run: $VaHome\.venv\Scripts\playwright.exe install chromium"
  }
}
```

- [ ] **Step 3: Update extras list to include `browser` and `memory`**

```bash
EXTRAS="audio,gmail,web,memory,browser"
if [ -z "${VA_NO_DESKTOP:-}" ]; then EXTRAS="$EXTRAS,desktop"; fi
```

(Same on PowerShell side.)

- [ ] **Step 4: Commit**

```bash
git add scripts/install.sh scripts/install.ps1
git commit -m "feat(install): include memory + browser extras and Chromium binary"
```

---

## Task 11: README + final verification + push

- [ ] **Step 1: Update README with the new capabilities**

Append a "Tools" section listing browser, whatsapp, memory, history.

- [ ] **Step 2: All tests + lint + types**

```bash
~/.local/share/voice-assistant/.venv/bin/pytest -q
~/.local/share/voice-assistant/.venv/bin/ruff check src/ tests/
~/.local/share/voice-assistant/.venv/bin/mypy src/voice_assistant
```

- [ ] **Step 3: Build frontend**

```bash
cd web && npm run build
```

- [ ] **Step 4: Reinstall + smoke launch**

```bash
~/.local/share/voice-assistant/.venv/bin/pip install -e /home/zeeshan-ahmed/voice-assistant --no-deps
~/.local/share/voice-assistant/.venv/bin/pip install loguru sqlite-vec playwright
~/.local/share/voice-assistant/.venv/bin/playwright install chromium
pkill -f "voice-assistant --gui" 2>/dev/null; sleep 1
DISPLAY=:0 ~/.local/share/voice-assistant/.venv/bin/voice-assistant --gui --config ~/.voice-assistant/config.yaml &
```

- [ ] **Step 5: Push**

```bash
git push origin main
```

---

## Done criteria

- `pytest -q` passes (~150+ tests).
- `ruff check` and `mypy --strict` pass cleanly.
- `voice-assistant --gui` shows previous conversation history on open.
- Asking "remember that my work email is X" calls the `remember` tool; later asking "what's my work email" calls `recall` and answers correctly.
- Asking "send a WhatsApp to +923001234567 saying 'hi'" launches Playwright's Chromium, waits for the user to scan a QR code (first time), then sends the message.
- GitHub Actions CI is green on the next push.
