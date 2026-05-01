# Bug fixes + wake-word + UI overhaul

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use `- [ ]` syntax.

**Goal:** Three coordinated phases: (1) fix the broken voice/avatar/multilingual flow, (2) add always-on wake-word listening, (3) redesign the GUI to be modern, responsive, animated, and visibly professional.

## Phase 1 — Bug fixes

### Bug 1: Avatar SVG doesn't load (file:// + absolute path)

`Avatar.ts` references `/avatars/aria.svg`. Pywebview loads `index.html` via `file://` and `/avatars/...` resolves to `file:///avatars/aria.svg` — missing.

**Fix:** Use relative path `avatars/aria.svg` (no leading slash). All three avatar SVGs.

```ts
// web/src/components/Avatar.ts
const AVATAR_SRC: Record<string, string> = {
  aria: 'avatars/aria.svg',
  liam: 'avatars/liam.svg',
  sage: 'avatars/sage.svg',
};
```

### Bug 2: Settings drawer save loses voice/avatar/stt_language

`bridge.save_config` builds `WizardAnswers(...)` but doesn't pass through `voice`, `avatar`, `stt_language`. So picking "Nova (Urdu)" in the drawer reverts to default Piper at save time.

**Fix:** `bridge.save_config` extracts these from incoming `cfg` dict and passes them to `WizardAnswers`.

```python
# src/voice_assistant/desktop/bridge.py — in save_config
answers = WizardAnswers(
    provider=provider,
    model=cfg["model"],
    hotkey=cfg["hotkey"],
    allowed_roots=roots,
    ollama_base_url=cfg.get("ollama_base_url"),
    user_name=cfg.get("user_name") or None,
    user_address_as=cfg.get("user_address_as") or "none",
    user_title=cfg.get("user_title") or None,
    voice=cfg.get("voice") or "piper:en_US-amy-medium",
    stt_language=cfg.get("stt_language") or "auto",
    avatar=cfg.get("avatar") or "aria",
)
```

Also: `_config_to_dict` must return these fields (some may already be there from Task 5b895de — verify all three are present).

### Bug 3: Language rule too soft

Current system prompt: *"Always respond in the same language the user used."* Models often default to English regardless. Two changes:

1. **Strengthen the system rule** — explicit example, top of the prompt.
2. **Add a force-language config option** — `user.respond_in: "auto" | <iso-code>`. When set to a specific code, override auto-detection.

```python
# src/voice_assistant/brain.py — _build_system_prompt
def _build_system_prompt(user: UserConfig | None) -> str:
    address_line = ""
    language_line = (
        "Detect the language of the user's most recent message and respond in that exact "
        "language. If they wrote in Urdu, reply in Urdu. If Hindi, reply in Hindi. "
        "If Czech, Czech. Do not default to English unless the user wrote in English. "
        "Switch languages immediately when the user does.\n"
    )
    if user and user.respond_in and user.respond_in != "auto":
        language_line = (
            f"Always respond in {user.respond_in} regardless of what language the user used. "
            "Translate your response if needed.\n"
        )
    # ... rest unchanged
```

Add to `UserConfig`:

```python
class UserConfig(BaseModel):
    name: str | None = None
    address_as: Literal["first_name", "full_name", "title", "none"] = "none"
    title: str | None = None
    respond_in: str = "auto"   # "auto" or ISO code
```

Add to `WizardAnswers` and `render_config`. Add a "Reply language" picker in Settings (24 languages + auto).

---

## Phase 2 — Wake-word always-on listening

### Tech

`openwakeword` — Apache 2.0, no license keys, ships with built-in models (`hey_jarvis`, `alexa`, `hey_mycroft`, `hey_rhasspy`, `weather`, `timer`).

```toml
# pyproject.toml — new optional extra
wake = ["openwakeword>=0.6", "onnxruntime>=1.17"]
```

### Architecture

A new `wake.py` module:

```python
# src/voice_assistant/wake.py
"""Always-on wake-word listener.

Runs on a background thread; samples the mic in 80ms chunks; feeds them
into openwakeword. When detection score crosses the threshold, fires the
provided callback (which the GUI uses to trigger record_and_respond).
"""
class WakeWordListener:
    def __init__(self, *, wake_word: str = "hey_jarvis", sensitivity: float = 0.5,
                 on_wake: Callable[[], None]) -> None: ...

    def start(self) -> None: ...
    def stop(self) -> None: ...
```

### Config

```python
class AudioConfig(BaseModel):
    trigger: Literal["hotkey", "wake_word"] = "hotkey"
    hotkey: str = "ctrl+shift+space"
    silence_seconds: float = 1.5
    wake_word: str = "hey_jarvis"
    wake_sensitivity: float = 0.5
```

### CLI wiring

In `_run_gui_mode`, branch on `cfg.audio.trigger`:

```python
if cfg.audio.trigger == "hotkey":
    listener = HotkeyListener(cfg.audio.hotkey)
    threading.Thread(target=lambda: hotkey_loop(listener, _on_listen_start), daemon=True).start()
elif cfg.audio.trigger == "wake_word":
    from voice_assistant.wake import WakeWordListener
    wake = WakeWordListener(
        wake_word=cfg.audio.wake_word,
        sensitivity=cfg.audio.wake_sensitivity,
        on_wake=_on_listen_start,
    )
    wake.start()
```

### Settings UX

In Audio section:
- Trigger: `Hotkey` | `Wake word`
- If hotkey: existing input
- If wake word: dropdown of (`hey_jarvis`, `alexa`, `hey_mycroft`) + sensitivity slider 0-1

### Install

`scripts/install.sh` adds `wake` to extras: `EXTRAS="audio,gmail,web,memory,browser,wake"`.

---

## Phase 3 — UI overhaul

### Vision

Modern chat-app aesthetic. Three changes that compound:

1. **Chat-bubble transcript** instead of "you / assistant" side-by-side rows.
2. **Glassmorphism + animated gradient** background — subtle violet pan.
3. **Reorganised layout** with a left-side conversation panel (resizable) when the window is wide enough.

### Layout breakpoints

| Width | Layout |
|---|---|
| ≥ 1024px | Two-pane: left = conversation panel, right = avatar/composer |
| 768-1023 | Single column, conversation as scrollable list above composer |
| < 768px | Single column, header collapses, composer fixed bottom |

### New components

#### `web/src/components/Background.ts`

Animated gradient: two radial blobs slowly panning in opposite directions. CSS-only (no JS animation loop). Uses `prefers-reduced-motion` to disable motion when requested.

#### `web/src/components/ChatTranscript.ts`

Replaces the existing `Transcript` class for the rendered output. Each turn becomes a chat bubble:

- User: right-aligned, violet background (`bg-accent/20`), rounded-2xl, max-w-[70%]
- Assistant: left-aligned, surface background, with avatar thumbnail, rounded-2xl
- Tool calls: small italic line below the assistant bubble: `↳ web_search("…")`
- Streaming chunks: append to current assistant bubble; subtle "typing" cursor at the end

Smooth fade+slide-up entrance (existing `.reveal` pattern).

#### `web/src/components/Composer.ts` (rewrite)

- Rounded full-width pill input with the mic button inside on the left
- Send button on the right (paper-airplane icon, only visible when input has text)
- Mic button changes state: idle (mic icon), listening (pulsing red dot)
- Auto-resize textarea (1-4 lines) instead of single-line input
- Enter sends, Shift+Enter inserts newline

#### `web/src/components/ListeningWave.ts`

20 vertical bars, each animated with random offsets. Visible only when `state == "listening"`. Replaces the static "Listening…" text below the avatar with a living visual.

#### `web/src/components/HistoryPanel.ts` (new, ≥1024px only)

Left-side resizable column. Lists the conversation chronologically (already in `history.jsonl`). On click — scrolls the transcript to that turn. Future: search field at the top.

#### `web/src/components/Settings.ts` (rewrite — tabs)

Drawer becomes tabbed:

- **Brain** (provider, model, key, reply-language)
- **Voice** (avatar, voice, STT language)
- **Audio** (trigger: hotkey/wake-word, hotkey/wake-word config)
- **Identity** (name, address-as, title)
- **Privacy** (allowed folders)

Tabs vertical on left, content fills right. Far more scannable than the current scroll-soup.

### Animation system

A small `web/src/anim.ts` exposing helpers:

- `mountReveal(el)` — adds `.reveal.is-visible` after intersection (existing).
- `mountBob(el, speed)` — slow vertical bob during state x.

All transitions: `200ms cubic-bezier(0.2, 0.8, 0.2, 1)`. Respect `prefers-reduced-motion`.

### Theme refinement

Background: not pure `#0b0d10` — slight gradient `linear-gradient(135deg, #0b0d10 0%, #15101f 50%, #0b0d10 100%)` with a low-opacity violet radial blob slowly moving. Visible but never distracting.

Surface cards: `bg-surface/60 backdrop-blur-md border border-border` for the glassmorphism feel.

---

## Tasks

### Task 1: Fix avatar path + voice/avatar/stt persistence + strengthen language rule

**Files:**
- Modify: `web/src/components/Avatar.ts` — relative paths
- Modify: `src/voice_assistant/desktop/bridge.py` — pass voice/avatar/stt to WizardAnswers
- Modify: `src/voice_assistant/config.py` — `UserConfig.respond_in`
- Modify: `src/voice_assistant/setup_wizard.py` — `WizardAnswers.respond_in`, render
- Modify: `src/voice_assistant/brain.py` — stronger language rule, force-language path
- Add tests covering the WizardAnswers + bridge round-trip

Commit: `fix(desktop): avatar SVG path + Settings save persists voice/avatar/STT/respond-in + stronger language rule`

### Task 2: openWakeWord integration

**Files:**
- Create: `src/voice_assistant/wake.py`
- Create: `tests/test_wake.py` (mock the openwakeword model)
- Modify: `pyproject.toml` — `wake` extra
- Modify: `src/voice_assistant/config.py` — AudioConfig.trigger=wake_word + new fields
- Modify: `src/voice_assistant/setup_wizard.py` — render trigger/wake_word/sensitivity
- Modify: `src/voice_assistant/desktop/bridge.py` — return + persist trigger config
- Modify: `src/voice_assistant/cli.py` — branch on trigger; start WakeWordListener
- Modify: `scripts/install.sh` / `install.ps1` — add `wake` extra

Commit: `feat(wake): always-on wake-word listening via openWakeWord (hey_jarvis, alexa, hey_mycroft)`

### Task 3: UI overhaul — Background + ChatTranscript + ListeningWave

**Files:**
- Create: `web/src/components/Background.ts`
- Create: `web/src/components/ChatTranscript.ts` (replaces Transcript)
- Create: `web/src/components/ListeningWave.ts`
- Modify: `web/src/main.ts` — wire new components
- Modify: `web/src/style.css` — keyframes, glass utilities

Commit: `feat(ui): chat-bubble transcript + animated gradient + listening waveform`

### Task 4: UI overhaul — Composer rewrite + HistoryPanel

**Files:**
- Modify: `web/src/components/Composer.ts` — rewrite (textarea, mic-state, send)
- Create: `web/src/components/HistoryPanel.ts`
- Modify: `web/src/main.ts` — responsive grid

Commit: `feat(ui): composer rewrite (auto-grow textarea) + history sidebar (≥1024px)`

### Task 5: UI overhaul — Settings tabs

**Files:**
- Modify: `web/src/components/Settings.ts` — tab nav + per-tab content
- Reuse all existing fields, add reply-language picker, add wake-word controls

Commit: `feat(ui): tabbed settings drawer (Brain / Voice / Audio / Identity / Privacy)`

### Task 6: Verify + push

- pytest, ruff, mypy clean
- `cd web && npm run build`
- pip install editable + restart GUI
- Push origin/main

---

## Done criteria

- Avatar SVG renders correctly (no broken-image fallback).
- Picking `openai:nova` + Urdu reply-language in Settings → Save → next request actually speaks in Nova's voice and replies in Urdu.
- Switching trigger to "wake word" in Settings → Save → speaking "Hey Jarvis" triggers a recording without pressing any hotkey.
- Window at 800×600: usable single-column. At 1600×1000: two-pane with history on the left.
- All animations smooth, all transitions feel quick, glassmorphism visible on the avatar card and composer.
- pytest passes, ruff + mypy clean, ~190+ tests.
