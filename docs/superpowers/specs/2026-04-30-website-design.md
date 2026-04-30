# Voice-assistant marketing website — design

**Date:** 2026-04-30
**Status:** Approved
**Scope:** Single-page marketing site for the voice-assistant project, with per-OS install one-liners.

## Goal

A polished, eye-catching, fully responsive landing page that introduces voice-assistant to developers and gives them a one-command install path on macOS, Windows, or Linux. No docs site, no blog, no marketing funnel — just a confident product page that converts a visitor into a working install in under two minutes.

## Non-goals

- A documentation site (`/docs`, API reference, tutorials) — defer until there is a Phase 2.
- Native installers (`.dmg`, `.exe`, `.AppImage`) with code signing and notarisation — separate, larger project.
- Light-mode theme, internationalisation, blog, changelog, search.
- Analytics, A/B testing, newsletter signup, cookie banner.
- Mobile or web product surface — the assistant remains desktop-only.

## High-level decisions

| Decision | Choice | Why |
|---|---|---|
| Scope | Landing page only | Phase 1 personal-tool MVP; one page captures 90% of the value. |
| Install story | Per-OS one-liner scripts | Native-installer UX without months of signing/notarisation work. |
| Aesthetic | Modern minimal (Linear / Vercel-ish) | Best fit for a developer tool; eye-catching without gimmicks. |
| Tech stack | Astro + Tailwind | Static output, component reuse, zero JS by default, free deploy. |
| Hero centerpiece | Animated terminal demo | Shows real product behaviour in 3 seconds; CSS + tiny JS only. |

## Architecture

### Project layout

A new `website/` directory at the repo root, fully self-contained. The Python app under `src/` is untouched.

```
voice-assistant/
├── src/                          # existing Python app — untouched
├── scripts/
│   ├── install.sh                # canonical install script (macOS + Linux)
│   └── install.ps1               # canonical install script (Windows)
├── website/                      # NEW
│   ├── astro.config.mjs
│   ├── tailwind.config.cjs
│   ├── package.json
│   ├── public/
│   │   ├── favicon.svg
│   │   ├── og-image.png
│   │   └── install/                  # populated at build by prebuild script
│   │       ├── install.sh            # → /install.sh
│   │       └── install.ps1           # → /install.ps1
│   └── src/
│       ├── pages/index.astro
│       ├── layouts/Base.astro
│       ├── components/
│       │   ├── Nav.astro
│       │   ├── Hero.astro
│       │   ├── TerminalDemo.astro
│       │   ├── TrustStrip.astro
│       │   ├── Features.astro
│       │   ├── HowItWorks.astro
│       │   ├── InstallTabs.astro
│       │   ├── Safety.astro
│       │   ├── Faq.astro
│       │   └── Footer.astro
│       └── styles/global.css
```

### Single source of truth for install scripts

The canonical install scripts live in `scripts/install.sh` and `scripts/install.ps1`. A `prebuild` npm script copies them into `website/public/install/` before each Astro build, so the URLs `https://<site>/install.sh` and `https://<site>/install.ps1` always serve the version on `main`. Concretely, `website/package.json` has `"prebuild": "node scripts/copy-install-scripts.mjs"` (or an equivalent shell command) and the copied files are gitignored so the canonical pair in `scripts/` is the only checked-in copy.

### Deployment

Static output to `website/dist/`. Deploy free to Vercel, Cloudflare Pages, or GitHub Pages by pointing the platform at `website/`. No backend, no database, no runtime cost. Custom domain attaches later; the platform's free subdomain works initially.

## Page structure (top to bottom)

Single scrolling page, nine blocks. Each block has a heading + content; sections fade-up on scroll via IntersectionObserver (8px translate, once, respects reduced-motion).

1. **Nav** — sticky, transparent, becomes solid on scroll.
   - Left: wordmark `voice-assistant`.
   - Right: `Features` · `Install` · `Safety` · GitHub icon link.
   - ≤`md`: hamburger opens full-screen slide-in panel.

2. **Hero** — full viewport height.
   - Eyebrow: small all-caps tag, e.g. `PHASE 1 · OPEN SOURCE · LOCAL-FIRST`.
   - H1: ≤8 words, e.g. *"Talk to your computer."*
   - Subhead: one sentence, e.g. *"A local-first voice assistant that opens apps, manages files, and sends email — driven by the LLM of your choice."*
   - Primary CTA: `Install` (anchor jump to §6).
   - Secondary CTA: `View on GitHub`.
   - Animated terminal to the right ≥`lg`, below CTAs <`lg`.

3. **Trust strip** — small row: *"Powered by your choice of"* Claude · GPT · Gemini · Ollama. Reinforces user control and the pluggable-brain feature.

4. **Features** — 3×2 card grid (1 col ≤`sm`, 2 cols `sm–lg`, 3 cols ≥`lg`).
   - Voice in (hotkey + faster-whisper, 100% local).
   - LLM brain (pluggable: Claude / GPT / Gemini / Ollama).
   - Voice out (Piper TTS, local).
   - File tools (create/read/move/delete, path-scoped).
   - System tools (open URLs, launch apps).
   - Email (Gmail OAuth, `gmail.send` scope only).

5. **How it works** — horizontal four-step flow ≥`md`, vertical stack with down-arrows ≤`md`.
   `Hotkey → Transcribe → Decide → Act + Reply`, one-line caption per step.

6. **Install** — the conversion centerpiece.
   - Three OS tabs: **macOS · Windows · Linux** (auto-selected via `navigator.userAgentData.platform` with `navigator.platform` fallback). Tabs become full-width segmented pills ≤`sm`.
   - Each tab: prerequisites → one-line install command (with copy-to-clipboard button) → run command + hotkey note.
   - `<details>` disclosure: *"Or install from source"* — manual `git clone` + `pip install -e ".[audio,gmail,dev]"`.

7. **Safety** — single dark panel, four bullets: path-scoped filesystem · destructive-op confirmation · delete rate limit · prompt-injection defence. Quiet, technical tone.

8. **FAQ** — accordion, max 720px wide, centred. Six questions:
   - Is my voice sent to the cloud?
   - Which LLM should I use?
   - Does it work offline?
   - How do I revoke Gmail access?
   - How do I uninstall?
   - Why no mobile/web version?

9. **Footer** — repo link, license, "made by Zeeshan Ahmed", year. Stacked ≤`md`, single row ≥`md`.

## Animated terminal (hero centerpiece)

Stylised terminal: rounded corners, 1px border, soft shadow, faint grid background. Three traffic-light dots top-left. Title bar reads `voice-assistant — ~`. Monospace body, ~16px desktop / 14px mobile, comfortable line-height.

### Loop (~12s, restarts indefinitely)

| Time | Line | Effect |
|---|---|---|
| 0.0s | `$ voice-assistant` | typed char-by-char |
| 1.5s | `● Listening… press ctrl+shift+space` | fade-up |
| 3.0s | `🎙 "Create a folder called notes on my desktop"` | VU meter pulses 3.0–4.0s |
| 4.0s | `↳ transcribed` | dim text fade-up |
| 5.0s | `brain → tool: create_folder(path="~/Desktop/notes")` | typed char-by-char |
| 6.5s | `✓ folder created` | green checkmark fade-up |
| 7.5s | `🔊 "Done. Created notes on your desktop."` | speaker icon pulses |
| 9.5s | `● Listening…` | fade-up |
| 12.0s | (clear, restart) |  |

### Animation technique

Pure CSS animations plus a tiny vanilla-JS typewriter (≈40 lines, deferred). No video, no canvas, no animation libraries.

Three details that make it feel alive:
- Cursor blink only on the line currently being typed.
- The 🎙 line shows a 20-bar horizontal "VU meter" pulsing on a sine wave during seconds 3.0–4.0.
- Output lines fade in with a 6px upward translate, never just appear.

### Accessibility

- `prefers-reduced-motion: reduce` → animation freezes on the final frame (the completed exchange), still readable.
- The full transcript is embedded in the DOM with `aria-label="Demo of voice-assistant creating a folder by voice command"` so screen readers get the gist.
- No `aria-live` — we don't want the loop to announce repeatedly.

## Visual system

### Colour tokens (dark-mode default)

| Role | Token | Hex |
|---|---|---|
| Background | `bg` | `#0b0d10` |
| Surface | `surface` | `#13161b` |
| Border | `border` | `#1f242c` |
| Text | `fg` | `#e6e8eb` |
| Muted | `muted` | `#9aa3ad` |
| Dim | `dim` | `#6b7280` |
| Accent | `accent` | `#7c5cff` (violet) |
| Success | `success` | `#34d399` |
| Warning | `warn` | `#f59e0b` |

The accent (`#7c5cff`) is used for the primary CTA, headline highlight glyph, and link colour. WCAG AA contrast verified against `bg` for text use.

### Typography

- Display + body: **Inter** (variable, weights 400/500/600/700/800). Tight tracking (`-0.02em`) on H1/H2.
- Monospace: **JetBrains Mono** for terminal, code blocks, install commands.
- Self-hosted via `@fontsource` (Astro plugin); Latin subset only. No Google Fonts request.

### Type scale (fluid, mobile → desktop)

| Element | Value |
|---|---|
| H1 hero | `clamp(2.5rem, 6vw, 4.5rem)` |
| H2 section | `clamp(1.75rem, 3.5vw, 2.5rem)` |
| Body | `1rem` (`1.0625rem` ≥`md`) |
| Caption | `0.875rem` |

### Spacing

Tailwind defaults. Section vertical padding `py-24 md:py-32`.

### Motion

- Hover transitions: 200ms ease-out.
- Entrance transitions: 400ms `cubic-bezier(0.2, 0.8, 0.2, 1)`.
- IntersectionObserver-based section fade-up (8px translate, once).
- No parallax, no scroll-jacking, no autoplay video.
- Everything respects `prefers-reduced-motion: reduce`.

### Imagery

- One subtle radial gradient blob behind the hero (accent at 8% opacity, 120px blur).
- Section dividers are 1px hairlines.
- No stock illustrations, 3D graphics, or mascots.

## Install flow & per-OS scripts

### Install component behaviour

- Three tabs (macOS, Windows, Linux) with native-style glyphs.
- Auto-select via `navigator.userAgentData.platform`, falling back to `navigator.platform`. User can override by clicking another tab.
- Each tab shows three rows: **Prerequisites** (one line) → **Install** (single command in a code block with Copy button — clipboard API, button morphs to ✓ for 1.5s) → **Run** (`voice-assistant` plus a one-line hotkey note).
- Below the tabs: a `<details>` disclosure *"Or install from source"* revealing the manual `git clone` + `pip install -e ".[audio,gmail,dev]"` sequence.

### One-liner commands

```bash
# macOS / Linux
curl -fsSL https://<site>/install.sh | bash

# Windows (PowerShell)
iwr -useb https://<site>/install.ps1 | iex
```

### `install.sh` behaviour

POSIX-compliant bash, runs locally on the user's machine, ≈80 lines.

1. Detect OS + arch via `uname -s` / `uname -m`. Refuse if not `Darwin` or `Linux`.
2. Check Python ≥ 3.10. If missing or too old, print a clear message linking to python.org and exit; do not auto-install Python.
3. Linux only: check `portaudio` and `espeak-ng` are present (`pkg-config --exists portaudio-2.0` plus a `command -v espeak-ng` check). If missing, print the right command for the user's distro (`apt`, `dnf`, `pacman`) and exit cleanly. Never run `sudo` ourselves.
4. Pick install dir: `~/.local/share/voice-assistant`, honouring `$VA_HOME` if set.
5. Create venv: `python3 -m venv "$VA_HOME/.venv"`.
6. Install: `pip install --upgrade pip` then `pip install "voice-assistant[audio,gmail] @ git+https://github.com/<user>/voice-assistant"` (until a PyPI release exists).
7. Symlink launcher: `~/.local/bin/voice-assistant → "$VA_HOME/.venv/bin/voice-assistant"`. Warn if `~/.local/bin` is not on `PATH` and show how to add it.
8. Seed config: copy `config.yaml.example` to `~/.voice-assistant/config.yaml` if absent. Never overwrite.
9. Print next steps: *"Set your API key in `~/.voice-assistant/.env`, then run `voice-assistant`."*

### `install.ps1` behaviour

Equivalent on Windows: check `python.exe` ≥3.10, create venv, run `pip install`, add a Start Menu shortcut, seed config under `$env:APPDATA\voice-assistant\`.

### Hard rules

- Bash: `set -euo pipefail`. PowerShell: `$ErrorActionPreference = 'Stop'`. Fail loudly, never half-installed.
- No `sudo` or admin elevation. Everything installs into the user's home directory.
- The install page links to the source on GitHub so users can `curl ... | less` to audit before piping to `bash`.
- Print every action before performing it (`>>> creating venv at ...`).
- An `--uninstall` flag removes the venv and the launcher symlink, and asks before touching `~/.voice-assistant/` (which holds OAuth tokens and config).

### Out of scope

Code signing, notarisation, Homebrew/winget/AUR submissions, auto-update.

## Responsive strategy

### Breakpoints

| Name | Width | Anchor device |
|---|---|---|
| `sm` | ≥640px | large phone landscape |
| `md` | ≥768px | tablet portrait |
| `lg` | ≥1024px | small laptop |
| `xl` | ≥1280px | standard desktop |
| `2xl` | ≥1536px | large monitor |

### Adaptations

- **Nav:** hamburger ≤`md`, full row ≥`md`. Hamburger opens a full-screen panel, not a tiny dropdown.
- **Hero:** single column ≤`lg` (headline → CTAs → terminal). Two columns ≥`lg` with terminal at ~55% width.
- **Features:** 1 col ≤`sm`, 2 cols `sm–lg`, 3 cols ≥`lg`.
- **How it works:** vertical stack with down-arrows ≤`md`, horizontal flow ≥`md`.
- **Install tabs:** segmented pills ≤`sm`, regular tabs ≥`sm`. Code block scrolls horizontally; never wraps.
- **FAQ:** full-width ≤`md`, centred max-720px ≥`md`.
- **Footer:** stacked ≤`md`, single row ≥`md`.

### Touch targets

Every interactive element ≥44×44px. Tab buttons get extra padding on mobile.

## Performance & accessibility

### Performance budget

- LCP ≤ 1.8s on simulated 4G.
- Total transferred ≤ 200 KB on first load (HTML + critical CSS + subset fonts + minimal JS).
- Zero blocking JS — animations are CSS, the typewriter is deferred.
- Self-hosted fonts, Latin subset only.
- Hero gradient is CSS — no images required for first paint.
- `<img>` tags use `loading="lazy"` and explicit `width`/`height` to prevent CLS.

### Accessibility budget

- WCAG 2.1 AA contrast on every text/background pair (the violet CTA on `bg` passes).
- Every interactive element keyboard-reachable with a visible focus ring.
- All animation respects `prefers-reduced-motion`.
- Lighthouse a11y score ≥95.

## Testing

- **Visual breakpoints:** manually verify at 360 / 414 / 768 / 1024 / 1440 / 1920 widths in Chrome DevTools device toolbar.
- **Lighthouse CI** in `npm run check`. Fails the build below: Performance 90, Accessibility 95, SEO 95, Best Practices 95.
- **Astro check:** `astro check` for `.astro` type errors.
- **Tailwind purge sanity:** verify final CSS < 30 KB.
- **Install scripts:** `shellcheck scripts/install.sh`, `Invoke-ScriptAnalyzer scripts/install.ps1`. Manual end-to-end install test on at least macOS or Linux before launch.
- **No automated browser tests** for the website itself — Playwright is overkill for a static landing page.

## Open questions / deferred decisions

- **Domain:** to be chosen before launch. Site works on the platform's free subdomain until then.
- **GitHub repo URL:** the install script's `pip install` line embeds the repo URL. The exact GitHub user/org slug needs to be set when scripts are written.
- **Headline copy:** *"Talk to your computer."* is a placeholder direction; final copy can be tuned at implementation time.
- **OG image:** a static `og-image.png` will be designed during implementation (1200×630, dark background with wordmark + tagline).
