# Desktop app — design

**Date:** 2026-04-30
**Status:** Approved
**Scope:** A `voice-assistant --gui` mode that opens a native desktop window with a live status orb, transcript, text-input fallback, and a settings drawer. Reuses the website's visual system. Wraps the existing orchestrator unchanged.

## Goal

Eliminate the terminal as the runtime UX. After installation, a user runs `voice-assistant`, gets a polished desktop window matching the marketing site, and never has to keep a terminal open to use voice mode. The hotkey continues to work system-wide; the window is a visual output surface.

## Non-goals

- System tray / menu-bar icon — phase 2.
- Multiple windows, multiple accounts, plugin system, custom themes, light-mode.
- Code-signed installers (`.dmg`, `.exe`, `.AppImage`), notarisation, App Store submissions.
- Conversation history persistence beyond the running session.
- Auto-update.
- Replacing the CLI — `voice-assistant --text` and `voice-assistant --setup` continue to work unchanged.

## High-level decisions

| Decision | Choice | Why |
|---|---|---|
| Tech approach | PyWebView + reused design system | Python core stays authoritative; the window IS our website's design language. Cohesive brand. |
| Frontend stack | Vite + TypeScript + Tailwind 3 | Small bundle, no framework overhead, reuses website's `tailwind.config.cjs` tokens. |
| Bundle delivery | npm prebuild → `web/dist/` shipped as Python package_data | Single `pip install` puts everything in place; no separate frontend deploy. |
| Bridge | PyWebView `js_api` (bidirectional in-process) | Zero network, zero auth, zero ports. Survives sleep/wake cleanly. |
| Default mode | Auto-detect GUI on graphical sessions; CLI fallback | Headless Linux (SSH, Docker without -it) keeps the existing experience. |
| Hotkey | Existing `pynput` listener, system-wide | Unchanged. Window doesn't need focus to react. |
| Settings | Slide-out drawer; same fields as wizard | One config surface, two skins (terminal wizard + drawer). |

## Architecture

### Project layout

```
voice-assistant/
├── src/voice_assistant/
│   ├── desktop/                     # NEW
│   │   ├── __init__.py
│   │   ├── window.py                # PyWebView window factory + lifecycle
│   │   ├── bridge.py                # JS-callable Python API (no UI logic)
│   │   └── events.py                # Pub-sub: orchestrator/audio → UI events
│   ├── cli.py                       # MODIFIED — add --gui / --no-gui
│   ├── app.py                       # MODIFIED — emit events into the bus
│   └── ... (existing modules untouched)
├── web/                             # NEW desktop frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.cjs          # imports website/tailwind tokens
│   ├── postcss.config.cjs
│   ├── index.html
│   └── src/
│       ├── main.ts                  # entry; wires bridge + components
│       ├── style.css                # @fontsource imports + Tailwind
│       ├── bridge.ts                # JS half of Python ↔ JS bridge
│       ├── state.ts                 # tiny finite-state machine
│       └── components/
│           ├── Orb.ts               # the centerpiece
│           ├── Header.ts
│           ├── Transcript.ts
│           ├── Composer.ts
│           ├── Settings.ts
│           └── Toast.ts             # transient notifications
├── tests/test_desktop_bridge.py     # NEW — pure-Python bridge tests
├── pyproject.toml                   # add `desktop` extra; ship web/dist as package_data
└── scripts/install.sh               # install desktop extras by default
```

### Process model

```
┌────────────────────────────────────────────────┐
│  voice-assistant --gui                         │
│                                                │
│   ┌──────────────────────────────────────┐     │
│   │  Python process (1 thread per role)  │     │
│   │                                      │     │
│   │  ┌──────────────────────────────┐    │     │
│   │  │ Orchestrator                 │    │     │
│   │  │  (existing)                  │    │     │
│   │  └────────────┬─────────────────┘    │     │
│   │               │ events bus           │     │
│   │  ┌────────────▼─────────────────┐    │     │
│   │  │ Bridge (JS-callable)         │    │     │
│   │  └────────────┬─────────────────┘    │     │
│   │               │ webview.evaluate_js  │     │
│   │  ┌────────────▼─────────────────┐    │     │
│   │  │ PyWebView Window (1)         │    │     │
│   │  └────────────┬─────────────────┘    │     │
│   │               │ rendered by          │     │
│   │  ┌────────────▼─────────────────┐    │     │
│   │  │ web/dist/index.html (static) │    │     │
│   │  └──────────────────────────────┘    │     │
│   └──────────────────────────────────────┘     │
└────────────────────────────────────────────────┘
```

Single Python process. PyWebView starts the GUI thread; orchestrator runs on a worker thread. The bridge marshals events between them.

### Bridge contract

The Python class `Bridge` is exposed to the webview as `window.pywebview.api`. Methods are JSON-serialisable.

```python
class Bridge:
    def start_listening(self) -> None
    def stop_listening(self)  -> None
    def send_text(self, text: str) -> None
    def get_config(self)      -> dict     # current config.yaml as nested dict
    def save_config(self, cfg: dict) -> dict  # returns {"ok": bool, "errors": [...]}
    def open_settings(self)   -> None     # no-op stub for keyboard shortcut → JS
    def quit(self)            -> None
```

Python → JS events are pushed via `webview.windows[0].evaluate_js("window.va.emit(<json>)")`. The TypeScript event union:

```ts
type VAEvent =
  | { type: 'status';      value: 'idle'|'listening'|'thinking'|'speaking'|'error' }
  | { type: 'transcript';  speaker: 'user'|'assistant'; text: string; tool_call?: string }
  | { type: 'audio_level'; rms: number }      // 0..1, for the orb animation
  | { type: 'config';      cfg: AppConfig }   // pushed when config is hot-reloaded
  | { type: 'toast';       level: 'info'|'warn'|'error'; message: string };
```

`audio_level` events are throttled to 30 Hz to keep the bridge cheap.

### CLI surface

```python
parser.add_argument("--gui",     action="store_true", help="Force desktop window mode.")
parser.add_argument("--no-gui",  action="store_true", help="Force CLI mode even with a display.")
# --text and --setup remain unchanged.
```

Mode resolution:
1. If `--setup` → wizard (current behaviour).
2. If `--text` or `--no-gui` → CLI loop (current behaviour).
3. If `--gui` → window.
4. Else: auto-detect — open window if `$DISPLAY` or `$WAYLAND_DISPLAY` (Linux), `os.environ.get("TERM_PROGRAM")` is *not* the only graphical signal (mac/Windows always have a session), `pywebview` import succeeds, and `web/dist/index.html` exists. Otherwise fall through to CLI.

The auto-detect is permissive: any failure path drops to CLI rather than crashing.

### Frontend

Vite-built static SPA. No framework. Components are plain TypeScript classes that own a slice of the DOM and expose `mount(parent)` / `update(state)` / `destroy()`.

A tiny FSM in `state.ts`:

```
idle ──start_listening──► listening ──stop──► thinking ──reply──► speaking ──end──► idle
                                       └──error──┐
                                                 ▼
                                               error → idle (after 2s)
```

The Orb subscribes to state + `audio_level`; everything else updates from `transcript` and `status` events.

### The Orb

A single `<canvas>` (256×256) with three layered rendering passes:

1. Soft violet halo (radial gradient on the canvas, blur via CSS `filter: blur(40px)` on a sibling layer).
2. Animated centre disc — pulsates with a 4-second sinusoid in idle, scales with `audio_level` in listening, rotates a small arc in thinking, pulses with a faster sinusoid in speaking.
3. Reactive accent ring — only visible during listening/speaking, drawn from FFT bins at 60fps.

Audio-level data: in `listening` state the JS asks the page's `<audio>`/`MediaStream` for an `AnalyserNode`. In Python's `audio_input` module, the existing recording emits RMS samples that the bridge forwards to JS as `audio_level` events at 30 Hz. JS uses whichever source is available (Python is authoritative because it owns the mic; `MediaStream` would require duplicate device access).

### Settings drawer

Same fields as the setup wizard. On save:

1. JS calls `bridge.save_config(cfg_dict)`.
2. Python validates with `voice_assistant.config.Config.model_validate(cfg_dict)`.
3. On success, writes `~/.voice-assistant/config.yaml` and the API key to `~/.voice-assistant/.env` (mode `0600`, stale managed-keys stripped — same `render_env()` already shipped).
4. The orchestrator hot-reloads its config — no restart required for: provider, model, hotkey, allowed_roots. Audio device changes trigger a soft reset of the listener.
5. JS receives a fresh `config` event and updates the drawer.

Errors return `{ok: false, errors: [...]}` and surface as a toast.

### Visual system

Identical to the website's tokens:

| Role | Hex |
|---|---|
| `bg` | `#0b0d10` |
| `surface` | `#13161b` |
| `border` | `#1f242c` |
| `fg` | `#e6e8eb` |
| `muted` | `#9aa3ad` |
| `dim` | `#7d8590` |
| `accent` | `#9580ff` |
| `success` | `#34d399` |
| `warn` | `#f59e0b` |

Inter for type, JetBrains Mono for the transcript when showing tool calls. Same `.reveal` IntersectionObserver pattern for transcript-line entrance.

The Tailwind config in `web/` extends the website's config rather than duplicating it (`require("../website/tailwind.config.cjs")` then merges any web-specific tokens).

## Distribution

`pyproject.toml` adds:

```toml
[project.optional-dependencies]
desktop = ["pywebview>=5"]

[tool.setuptools.package-data]
voice_assistant = ["desktop/web_dist/**/*"]
```

Build flow:
1. `cd web && npm install && npm run build` → `web/dist/`
2. A `prebuild` script (Python `setup.py`-style or a tiny `tool.uv-build`) copies `web/dist/` into `src/voice_assistant/desktop/web_dist/` before `pip install` packages it.
3. `Window.__init__` resolves the bundled `web_dist/index.html` via `importlib.resources`.

Install scripts (`scripts/install.sh`, `scripts/install.ps1`) change one line:

```diff
- pip install "voice-assistant[audio,gmail] @ git+$REPO_URL"
+ pip install "voice-assistant[audio,gmail,desktop] @ git+$REPO_URL"
```

The desktop extra is opt-in for headless environments via `VA_NO_DESKTOP=1` env var (skipped at install time).

## Linux dependencies

PyWebView on Linux needs **GTK 3** + **WebKit2GTK**. Most desktop distros have these pre-installed. If they're missing, the install script adds a soft warning (analogous to the espeak-ng pattern):

```bash
if [ "$OS" = "Linux" ] && [ -z "${VA_NO_DESKTOP:-}" ]; then
  if ! pkg-config --exists webkit2gtk-4.1 webkit2gtk-4.0 2>/dev/null \
       && ! pkg-config --exists gtk+-3.0 2>/dev/null; then
    if   command -v apt-get >/dev/null; then warn "Desktop window needs WebKit2GTK + GTK3. Run: sudo apt-get install -y python3-gi gir1.2-webkit2-4.1 libgtk-3-0"
    elif command -v dnf     >/dev/null; then warn "Desktop window needs WebKit2GTK + GTK3. Run: sudo dnf install -y python3-gobject webkit2gtk4.1 gtk3"
    elif command -v pacman  >/dev/null; then warn "Desktop window needs WebKit2GTK + GTK3. Run: sudo pacman -S --needed python-gobject webkit2gtk-4.1 gtk3"
    fi
    warn "GUI may not start; falling back to CLI is automatic."
  fi
fi
```

macOS uses the system WebKit (no extra deps). Windows uses Edge WebView2 (auto-installed on Win10+ via Windows Update; missing on stripped builds — PyWebView 5 prompts a download).

## Error handling

| Failure | Behaviour |
|---|---|
| `import pywebview` fails | Auto-detect drops to CLI; explicit `--gui` prints "PyWebView not installed; pip install voice-assistant[desktop]" and exits 1. |
| `web_dist/index.html` missing | Same: drop to CLI on auto-detect; on `--gui` print a clear "frontend bundle missing — please reinstall" and exit 1. |
| Bridge call raises | JS receives `{type:'error', message:str}` toast; Python logs full traceback. |
| Config save validation fails | Toast in UI; old config remains on disk untouched. |
| Mic permission denied | Toast: "Microphone access blocked. Check OS settings." Status returns to idle. |
| Hotkey conflict | Soft warning in toast; user can change it in Settings. |
| Orchestrator crashes | Window stays alive; status goes to `error`; user can retry. Python logs the traceback. |

## Testing

- **Existing 107 tests** stay unchanged. Orchestrator, brain, safety, wizard, tools, etc.
- **New: `tests/test_desktop_bridge.py`** — pure-Python tests of:
  - `Bridge.get_config` returns a dict shaped like `Config`.
  - `Bridge.save_config` validates input, writes files, emits `config` event.
  - `Bridge.send_text` enqueues to the orchestrator.
  - Event-bus throttling (audio_level fires no more than 30/sec).
  - All bridge methods raise nothing (return `{ok: false}` on validation errors).
- **No JS tests.** The frontend logic is thin and visual; manual smoke covers it. (Playwright/Vitest is overkill for ~600 lines of TS.)
- **Manual smoke checklist** lands in `docs/superpowers/notes/desktop-smoke-checklist.md`:
  - Cold start (`voice-assistant --gui`) opens window in <2s.
  - Press hotkey: orb goes listening, RMS pulses match speech, transcript appears.
  - Click record button: same flow.
  - Type in composer + Enter: same flow without audio.
  - Open settings, swap provider, save — next request uses the new provider.
  - Close window: process exits cleanly.
  - On Linux without WebKit2GTK: auto-detect drops to CLI; `--gui` prints clear error.

## Performance budget

- Cold start (window visible, idle orb): ≤ 2s on a 2018 MacBook equivalent.
- Bridge round-trip: ≤ 5ms p95 (PyWebView in-process is sub-ms; budget covers JSON marshalling).
- Frontend bundle: ≤ 80 KB gzipped (Vite tree-shakes well; main weight is Inter subset).
- Memory at idle: ≤ 150 MB (PyWebView + Python + WebKit page).

## Open questions / deferred decisions

- **System tray icon** (Phase 2). Adds always-available presence; not in this scope.
- **Conversation persistence.** Currently the transcript clears on window close. Persisting to `~/.voice-assistant/history.jsonl` is a small follow-up.
- **Light mode toggle.** Defer until the website has it.
- **Keyboard shortcuts inside the window.** Initial set: `Cmd/Ctrl+,` opens Settings, `Esc` closes drawer, `Space` (when composer empty + window focused) records. Extensions deferred.
