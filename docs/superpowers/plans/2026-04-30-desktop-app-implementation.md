# Desktop App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the desktop app described in `docs/superpowers/specs/2026-04-30-desktop-app-design.md` — a `voice-assistant --gui` mode that opens a native window with a status orb, transcript, composer, and settings drawer. Reuses the website's design tokens. Wraps the existing orchestrator unchanged.

**Architecture:** Vite + TypeScript + Tailwind frontend at `web/` builds to a static bundle. PyWebView in a new `voice_assistant.desktop` module renders that bundle in a native webview. A bidirectional `Bridge` class exposes typed methods to JS and pushes events back. The orchestrator is hot-reloadable for live settings changes.

**Tech Stack:** Python 3.11+ · PyWebView 5 · Vite 5 · TypeScript 5 · Tailwind 3 · `@fontsource/inter` + `@fontsource/jetbrains-mono` · pytest with `monkeypatch` · pynput (existing) · pydantic (existing).

---

## File Structure

**Created:**

```
web/                                        # NEW frontend
├── package.json
├── tsconfig.json
├── vite.config.ts
├── postcss.config.cjs
├── tailwind.config.cjs                     # extends ../website/tailwind.config.cjs
├── index.html
└── src/
    ├── main.ts
    ├── style.css
    ├── bridge.ts                           # Python ↔ JS bridge wrapper
    ├── state.ts                            # FSM
    ├── types.ts                            # shared types: VAEvent, AppConfig
    └── components/
        ├── Orb.ts
        ├── Header.ts
        ├── Transcript.ts
        ├── Composer.ts
        ├── Settings.ts
        └── Toast.ts

src/voice_assistant/desktop/                # NEW Python module
├── __init__.py
├── window.py                               # PyWebView lifecycle
├── bridge.py                               # JS-callable Python API
├── events.py                               # Pub-sub between orchestrator/audio and bridge
└── web_dist/                               # populated by prebuild from web/dist/

tests/test_desktop_bridge.py                # NEW
tests/test_desktop_events.py                # NEW

scripts/copy-web-dist.mjs                   # NEW build helper
```

**Modified:**

- `pyproject.toml` — add `desktop` optional extra, package_data entry
- `src/voice_assistant/cli.py` — add `--gui` / `--no-gui` flags, auto-detect, dispatch
- `src/voice_assistant/app.py` — emit events into the bus; expose `reload_config`
- `scripts/install.sh` — add `desktop` extra to the pip install line + GTK/WebKit warning
- `scripts/install.ps1` — add `desktop` extra
- `MANIFEST.in` (create if missing) — include `web_dist/**`

---

## Task 1: Scaffold web/ frontend with shared Tailwind tokens

**Files:**
- Create: `web/package.json`
- Create: `web/tsconfig.json`
- Create: `web/vite.config.ts`
- Create: `web/postcss.config.cjs`
- Create: `web/tailwind.config.cjs`
- Create: `web/index.html`
- Create: `web/.gitignore`
- Create: `web/src/main.ts`
- Create: `web/src/style.css`

- [ ] **Step 1: Create `web/package.json`**

```json
{
  "name": "voice-assistant-desktop",
  "version": "0.0.1",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@fontsource/inter": "^5.0.18",
    "@fontsource/jetbrains-mono": "^5.0.20"
  },
  "devDependencies": {
    "@types/node": "^22.5.0",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.41",
    "tailwindcss": "^3.4.10",
    "typescript": "^5.5.4",
    "vite": "^5.4.0"
  }
}
```

- [ ] **Step 2: Create `web/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "skipLibCheck": true,
    "isolatedModules": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"]
  },
  "include": ["src"]
}
```

- [ ] **Step 3: Create `web/vite.config.ts`**

```ts
import { defineConfig } from 'vite';

export default defineConfig({
  base: './',                     // produces relative paths so file:// loading works
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    target: 'es2022',
    cssCodeSplit: false,          // single CSS file simplifies packaging
    rollupOptions: {
      output: { inlineDynamicImports: true }
    }
  }
});
```

- [ ] **Step 4: Create `web/postcss.config.cjs`**

```js
module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };
```

- [ ] **Step 5: Create `web/tailwind.config.cjs`** that extends the website's

```js
const websiteConfig = require('../website/tailwind.config.cjs');

/** @type {import('tailwindcss').Config} */
module.exports = {
  ...websiteConfig,
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx,html}'],
};
```

- [ ] **Step 6: Create `web/index.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="color-scheme" content="dark" />
    <title>voice-assistant</title>
  </head>
  <body class="bg-bg text-fg font-sans">
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 7: Create `web/src/style.css`**

```css
@import '@fontsource/inter/400.css';
@import '@fontsource/inter/500.css';
@import '@fontsource/inter/600.css';
@import '@fontsource/inter/700.css';
@import '@fontsource/jetbrains-mono/400.css';

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root { --color-accent: #9580ff; }
  html, body { height: 100%; }
  html { @apply bg-bg text-fg; -webkit-font-smoothing: antialiased; }
  body { @apply font-sans; overflow: hidden; }   /* desktop window: no body scroll */
  ::selection { background: theme('colors.accent'); color: theme('colors.bg'); }
  :focus-visible { outline: 2px solid theme('colors.accent'); outline-offset: 2px; border-radius: 4px; }
  button { font: inherit; }
}
```

- [ ] **Step 8: Create `web/src/main.ts`**

```ts
import './style.css';

const root = document.getElementById('app')!;
root.innerHTML = `
  <div class="h-screen grid place-items-center">
    <p class="text-muted">voice-assistant — booting...</p>
  </div>
`;
```

- [ ] **Step 9: Create `web/.gitignore`**

```
node_modules/
dist/
.DS_Store
```

- [ ] **Step 10: Install + verify**

```bash
cd web && npm install
npm run build
ls -la dist/
```

Expected: `dist/index.html` exists with bundled CSS and JS (~50-100 KB).

- [ ] **Step 11: Commit**

```bash
git add web/ web/.gitignore
git commit -m "feat(desktop): scaffold web/ frontend with shared Tailwind tokens"
```

---

## Task 2: Static layout — Header + Composer + Transcript shells

**Files:**
- Create: `web/src/components/Header.ts`
- Create: `web/src/components/Composer.ts`
- Create: `web/src/components/Transcript.ts`
- Modify: `web/src/main.ts`

- [ ] **Step 1: Create `web/src/components/Header.ts`**

```ts
export class Header {
  private el: HTMLElement;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('header');
    this.el.className = 'h-12 px-5 flex items-center justify-between border-b border-border bg-surface/40';
    this.el.innerHTML = `
      <div class="flex items-center gap-3">
        <span class="font-mono text-sm">voice-assistant</span>
        <span class="text-dim text-xs">·</span>
        <span data-status class="text-xs text-muted">idle</span>
      </div>
      <button data-settings aria-label="Settings"
        class="h-9 w-9 grid place-items-center rounded-md hover:bg-bg/40 transition-colors text-muted hover:text-fg">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
      </button>
    `;
    parent.appendChild(this.el);
  }

  setStatus(value: string): void {
    const node = this.el.querySelector<HTMLElement>('[data-status]');
    if (node) node.textContent = value;
  }

  onSettingsClick(handler: () => void): void {
    this.el.querySelector<HTMLButtonElement>('[data-settings]')!
      .addEventListener('click', handler);
  }
}
```

- [ ] **Step 2: Create `web/src/components/Transcript.ts`**

```ts
export type TranscriptLine = { speaker: 'user'|'assistant'; text: string; tool_call?: string };

export class Transcript {
  private el: HTMLElement;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('section');
    this.el.className = 'flex-1 overflow-y-auto px-5 py-4 space-y-3';
    this.el.innerHTML = `<p class="text-dim text-sm">Press the hotkey or type a command to start.</p>`;
    parent.appendChild(this.el);
  }

  push(line: TranscriptLine): void {
    if (this.el.querySelector('p.text-dim')) this.el.replaceChildren();
    const wrapper = document.createElement('div');
    wrapper.className = 'flex gap-3';
    const tag = line.speaker === 'user'
      ? '<span class="text-xs text-dim shrink-0 mt-0.5 w-16">you</span>'
      : '<span class="text-xs text-accent shrink-0 mt-0.5 w-16">assistant</span>';
    const body = document.createElement('p');
    body.className = 'text-sm leading-6 text-fg';
    body.textContent = line.text;
    wrapper.innerHTML = tag;
    wrapper.appendChild(body);
    if (line.tool_call) {
      const tc = document.createElement('pre');
      tc.className = 'text-xs text-muted font-mono ml-19 mt-1';
      tc.textContent = `↳ ${line.tool_call}`;
      wrapper.appendChild(tc);
    }
    this.el.appendChild(wrapper);
    this.el.scrollTop = this.el.scrollHeight;
  }
}
```

- [ ] **Step 3: Create `web/src/components/Composer.ts`**

```ts
export class Composer {
  private el: HTMLElement;
  private input: HTMLInputElement;
  private submitHandler: (text: string) => void = () => {};
  private recordHandler: () => void = () => {};

  constructor(parent: HTMLElement) {
    this.el = document.createElement('footer');
    this.el.className = 'p-4 border-t border-border bg-surface/40 flex gap-2';
    this.el.innerHTML = `
      <button data-record aria-label="Hold to record"
        class="h-11 w-11 shrink-0 grid place-items-center rounded-md border border-border bg-surface hover:border-accent/40 transition-colors">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <rect x="9" y="2" width="6" height="12" rx="3"/>
          <path d="M5 10v2a7 7 0 0 0 14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="22"/>
        </svg>
      </button>
      <input data-input type="text" placeholder="Type a command..."
        class="flex-1 h-11 px-4 rounded-md border border-border bg-bg text-fg placeholder:text-dim focus:outline-none focus:border-accent" />
    `;
    parent.appendChild(this.el);
    this.input = this.el.querySelector<HTMLInputElement>('[data-input]')!;
    this.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && this.input.value.trim()) {
        this.submitHandler(this.input.value.trim());
        this.input.value = '';
      }
    });
    this.el.querySelector<HTMLButtonElement>('[data-record]')!
      .addEventListener('click', () => this.recordHandler());
  }

  onSubmit(handler: (text: string) => void): void { this.submitHandler = handler; }
  onRecord(handler: () => void): void { this.recordHandler = handler; }
}
```

- [ ] **Step 4: Replace `web/src/main.ts`** with the layout

```ts
import './style.css';
import { Header } from './components/Header';
import { Transcript } from './components/Transcript';
import { Composer } from './components/Composer';

const root = document.getElementById('app')!;
root.className = 'h-screen flex flex-col';
root.innerHTML = '';

const header = new Header(root);
const transcript = new Transcript(root);
const composer = new Composer(root);

composer.onSubmit((text) => transcript.push({ speaker: 'user', text }));
composer.onRecord(() => header.setStatus('listening'));
header.onSettingsClick(() => console.log('settings'));
```

- [ ] **Step 5: Verify**

```bash
cd web && npm run build && ls dist/
```

Expected: build succeeds, `dist/index.html` references bundled JS+CSS.

- [ ] **Step 6: Commit**

```bash
git add web/src/components/ web/src/main.ts
git commit -m "feat(desktop): static layout — header, transcript, composer"
```

---

## Task 3: Orb component (the centerpiece)

**Files:**
- Create: `web/src/components/Orb.ts`
- Modify: `web/src/main.ts`

- [ ] **Step 1: Create `web/src/components/Orb.ts`**

```ts
export type OrbState = 'idle'|'listening'|'thinking'|'speaking'|'error';

export class Orb {
  private el: HTMLElement;
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private state: OrbState = 'idle';
  private rms: number = 0;
  private rafId: number | null = null;
  private startTime: number = performance.now();

  constructor(parent: HTMLElement) {
    this.el = document.createElement('div');
    this.el.className = 'flex-1 grid place-items-center relative';
    this.el.innerHTML = `
      <div class="absolute inset-0 pointer-events-none"
        style="background: radial-gradient(closest-side, rgba(149,128,255,0.10), transparent 60%); filter: blur(60px);"></div>
      <canvas data-orb width="384" height="384" class="relative"></canvas>
      <p data-hint class="absolute bottom-12 text-sm text-muted">Press the hotkey to talk</p>
    `;
    parent.appendChild(this.el);
    this.canvas = this.el.querySelector<HTMLCanvasElement>('[data-orb]')!;
    const ctx = this.canvas.getContext('2d');
    if (!ctx) throw new Error('canvas 2d context unavailable');
    this.ctx = ctx;
    this.loop();
  }

  setState(s: OrbState): void {
    this.state = s;
    const hint = this.el.querySelector<HTMLElement>('[data-hint]');
    if (hint) hint.textContent = {
      idle:      'Press the hotkey to talk',
      listening: 'Listening…',
      thinking:  'Thinking…',
      speaking:  'Speaking…',
      error:     'Something went wrong.',
    }[s];
  }

  setRms(v: number): void { this.rms = Math.max(0, Math.min(1, v)); }

  private loop = (): void => {
    const t = (performance.now() - this.startTime) / 1000;
    const w = this.canvas.width, h = this.canvas.height;
    this.ctx.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h / 2;
    const accent = 'rgba(149,128,255,';

    // base radius, breathes slowly in idle
    let radius = 90 + Math.sin(t * 1.2) * 4;
    if (this.state === 'listening') radius = 90 + 60 * this.rms;
    if (this.state === 'speaking')  radius = 90 + Math.sin(t * 6) * 12;
    if (this.state === 'thinking')  radius = 90;

    // soft outer halo
    const g1 = this.ctx.createRadialGradient(cx, cy, radius * 0.4, cx, cy, radius * 1.6);
    g1.addColorStop(0, accent + '0.50)');
    g1.addColorStop(1, accent + '0)');
    this.ctx.fillStyle = g1;
    this.ctx.beginPath();
    this.ctx.arc(cx, cy, radius * 1.6, 0, Math.PI * 2);
    this.ctx.fill();

    // inner disc
    const g2 = this.ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
    g2.addColorStop(0, accent + '0.95)');
    g2.addColorStop(1, accent + '0.45)');
    this.ctx.fillStyle = g2;
    this.ctx.beginPath();
    this.ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    this.ctx.fill();

    // thinking arc
    if (this.state === 'thinking') {
      this.ctx.strokeStyle = '#e6e8eb';
      this.ctx.lineWidth = 3;
      this.ctx.lineCap = 'round';
      this.ctx.beginPath();
      const start = (t * 2) % (Math.PI * 2);
      this.ctx.arc(cx, cy, radius + 16, start, start + Math.PI * 0.6);
      this.ctx.stroke();
    }

    // error flash
    if (this.state === 'error') {
      this.ctx.fillStyle = `rgba(245,158,11,${0.4 + 0.3 * Math.sin(t * 8)})`;
      this.ctx.beginPath();
      this.ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      this.ctx.fill();
    }

    this.rafId = requestAnimationFrame(this.loop);
  };

  destroy(): void {
    if (this.rafId !== null) cancelAnimationFrame(this.rafId);
  }
}
```

- [ ] **Step 2: Wire `Orb` into `web/src/main.ts`** (between header and composer; transcript becomes a small bottom panel)

Replace `web/src/main.ts` with:

```ts
import './style.css';
import { Header } from './components/Header';
import { Transcript } from './components/Transcript';
import { Composer } from './components/Composer';
import { Orb } from './components/Orb';

const root = document.getElementById('app')!;
root.className = 'h-screen flex flex-col';
root.innerHTML = '';

const header = new Header(root);
const orb = new Orb(root);
const transcript = new Transcript(root);
const composer = new Composer(root);

// Restrict transcript to a max height so the orb stays centered
const transcriptEl = root.children[2] as HTMLElement;
transcriptEl.classList.remove('flex-1');
transcriptEl.classList.add('max-h-48', 'shrink-0');

composer.onSubmit((text) => {
  transcript.push({ speaker: 'user', text });
  orb.setState('thinking');
  setTimeout(() => orb.setState('idle'), 800);  // demo only; replaced by bridge events later
});
composer.onRecord(() => orb.setState('listening'));
header.onSettingsClick(() => console.log('settings'));
```

- [ ] **Step 3: Build and verify**

```bash
cd web && npm run build
```

Run `npm run dev`, open http://localhost:5173, see the orb pulsing in idle. Click record button → orb expands. Type + Enter → orb goes thinking and back. Stop dev server.

- [ ] **Step 4: Commit**

```bash
git add web/src/components/Orb.ts web/src/main.ts
git commit -m "feat(desktop): orb component — animated centerpiece"
```

---

## Task 4: State machine + types + Settings drawer (static)

**Files:**
- Create: `web/src/types.ts`
- Create: `web/src/state.ts`
- Create: `web/src/components/Settings.ts`
- Create: `web/src/components/Toast.ts`

- [ ] **Step 1: Create `web/src/types.ts`**

```ts
export type Provider = 'anthropic'|'openai'|'gemini'|'ollama';

export interface AppConfig {
  provider: Provider;
  model: string;
  hotkey: string;
  allowed_roots: string[];
  ollama_base_url: string | null;
}

export type VAEvent =
  | { type: 'status';      value: 'idle'|'listening'|'thinking'|'speaking'|'error' }
  | { type: 'transcript';  speaker: 'user'|'assistant'; text: string; tool_call?: string }
  | { type: 'audio_level'; rms: number }
  | { type: 'config';      cfg: AppConfig }
  | { type: 'toast';       level: 'info'|'warn'|'error'; message: string };
```

- [ ] **Step 2: Create `web/src/state.ts`**

```ts
import type { VAEvent } from './types';

type Listener = (e: VAEvent) => void;

class Bus {
  private listeners: Listener[] = [];
  emit(e: VAEvent): void { for (const l of this.listeners) l(e); }
  on(l: Listener): () => void {
    this.listeners.push(l);
    return () => { this.listeners = this.listeners.filter(x => x !== l); };
  }
}

export const bus = new Bus();
```

- [ ] **Step 3: Create `web/src/components/Settings.ts`**

```ts
import type { AppConfig, Provider } from '../types';

export class Settings {
  private el: HTMLElement;
  private saveHandler: (cfg: AppConfig) => Promise<{ok: boolean; errors?: string[]}> = async () => ({ok: true});

  constructor(parent: HTMLElement) {
    this.el = document.createElement('aside');
    this.el.className = 'fixed inset-y-0 right-0 w-full max-w-md bg-surface border-l border-border translate-x-full transition-transform duration-200 ease-out z-30 flex flex-col';
    this.el.innerHTML = `
      <header class="h-12 px-5 flex items-center justify-between border-b border-border">
        <h2 class="font-semibold">Settings</h2>
        <button data-close class="h-9 w-9 grid place-items-center rounded-md hover:bg-bg/40 text-muted hover:text-fg">×</button>
      </header>
      <form data-form class="flex-1 overflow-y-auto p-5 space-y-5 text-sm">
        <div>
          <label class="block text-muted mb-1">Provider</label>
          <select data-field="provider" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg">
            <option value="anthropic">Anthropic Claude</option>
            <option value="openai">OpenAI GPT</option>
            <option value="gemini">Google Gemini</option>
            <option value="ollama">Ollama (local)</option>
          </select>
        </div>
        <div>
          <label class="block text-muted mb-1">Model</label>
          <input data-field="model" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" />
        </div>
        <div data-secret-row>
          <label class="block text-muted mb-1" data-secret-label>API key</label>
          <input data-field="secret" type="password" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" placeholder="sk-…" />
          <p class="text-xs text-dim mt-1">Stored in ~/.voice-assistant/.env, mode 0600.</p>
        </div>
        <div>
          <label class="block text-muted mb-1">Hotkey</label>
          <input data-field="hotkey" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" placeholder="ctrl+shift+space" />
        </div>
        <div>
          <label class="block text-muted mb-1">Allowed folders (comma-separated)</label>
          <input data-field="roots" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" placeholder="~" />
        </div>
        <div data-error class="hidden text-warn text-xs"></div>
      </form>
      <footer class="p-5 border-t border-border flex justify-end gap-2">
        <button data-cancel type="button" class="h-10 px-4 rounded-md border border-border text-fg hover:bg-bg/40">Cancel</button>
        <button data-save   type="button" class="h-10 px-4 rounded-md bg-accent text-bg font-semibold hover:opacity-90">Save</button>
      </footer>
    `;
    parent.appendChild(this.el);

    this.el.querySelector<HTMLButtonElement>('[data-close]')!.addEventListener('click', () => this.close());
    this.el.querySelector<HTMLButtonElement>('[data-cancel]')!.addEventListener('click', () => this.close());
    this.el.querySelector<HTMLSelectElement>('[data-field="provider"]')!.addEventListener('change', (e) => {
      const v = (e.target as HTMLSelectElement).value as Provider;
      const label = this.el.querySelector<HTMLElement>('[data-secret-label]')!;
      label.textContent = v === 'ollama' ? 'Ollama base URL' : 'API key';
      const input = this.el.querySelector<HTMLInputElement>('[data-field="secret"]')!;
      input.type = v === 'ollama' ? 'text' : 'password';
      input.placeholder = v === 'ollama' ? 'http://localhost:11434' : 'sk-…';
    });
    this.el.querySelector<HTMLButtonElement>('[data-save]')!.addEventListener('click', async () => {
      const cfg = this.read();
      const errEl = this.el.querySelector<HTMLElement>('[data-error]')!;
      const result = await this.saveHandler(cfg);
      if (result.ok) {
        errEl.classList.add('hidden');
        this.close();
      } else {
        errEl.textContent = (result.errors || ['Save failed']).join(' · ');
        errEl.classList.remove('hidden');
      }
    });
  }

  open(cfg: AppConfig): void {
    this.populate(cfg);
    this.el.classList.remove('translate-x-full');
  }

  close(): void {
    this.el.classList.add('translate-x-full');
  }

  onSave(handler: (cfg: AppConfig) => Promise<{ok: boolean; errors?: string[]}>): void {
    this.saveHandler = handler;
  }

  private populate(cfg: AppConfig): void {
    (this.el.querySelector('[data-field="provider"]') as HTMLSelectElement).value = cfg.provider;
    (this.el.querySelector('[data-field="model"]') as HTMLInputElement).value = cfg.model;
    (this.el.querySelector('[data-field="hotkey"]') as HTMLInputElement).value = cfg.hotkey;
    (this.el.querySelector('[data-field="roots"]') as HTMLInputElement).value = cfg.allowed_roots.join(', ');
    const secret = this.el.querySelector<HTMLInputElement>('[data-field="secret"]')!;
    secret.value = '';
    secret.placeholder = cfg.provider === 'ollama' ? (cfg.ollama_base_url || 'http://localhost:11434') : 'sk-…';
    secret.type = cfg.provider === 'ollama' ? 'text' : 'password';
    const label = this.el.querySelector<HTMLElement>('[data-secret-label]')!;
    label.textContent = cfg.provider === 'ollama' ? 'Ollama base URL' : 'API key';
  }

  private read(): AppConfig {
    const provider = (this.el.querySelector('[data-field="provider"]') as HTMLSelectElement).value as Provider;
    const model    = (this.el.querySelector('[data-field="model"]') as HTMLInputElement).value.trim();
    const hotkey   = (this.el.querySelector('[data-field="hotkey"]') as HTMLInputElement).value.trim();
    const roots    = (this.el.querySelector('[data-field="roots"]') as HTMLInputElement).value
      .split(',').map(s => s.trim()).filter(Boolean);
    const secret   = (this.el.querySelector('[data-field="secret"]') as HTMLInputElement).value.trim();
    return {
      provider, model, hotkey,
      allowed_roots: roots,
      ollama_base_url: provider === 'ollama' ? (secret || 'http://localhost:11434') : null,
      ...(provider !== 'ollama' && secret ? { _secret: secret } as object : {}) as object,
    } as AppConfig & { _secret?: string };
  }
}
```

- [ ] **Step 4: Create `web/src/components/Toast.ts`**

```ts
type Level = 'info'|'warn'|'error';

export class Toast {
  private el: HTMLElement;
  private timer: number | null = null;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('div');
    this.el.className = 'fixed top-16 left-1/2 -translate-x-1/2 px-4 py-2 rounded-md text-sm font-medium opacity-0 pointer-events-none transition-opacity duration-200 z-40';
    parent.appendChild(this.el);
  }

  show(level: Level, message: string): void {
    if (this.timer !== null) clearTimeout(this.timer);
    const colors: Record<Level, string> = {
      info:  'bg-surface border border-border text-fg',
      warn:  'bg-warn/10 border border-warn/40 text-warn',
      error: 'bg-warn/10 border border-warn/40 text-warn',
    };
    this.el.className = `fixed top-16 left-1/2 -translate-x-1/2 px-4 py-2 rounded-md text-sm font-medium opacity-100 transition-opacity duration-200 z-40 ${colors[level]}`;
    this.el.textContent = message;
    this.timer = window.setTimeout(() => {
      this.el.classList.replace('opacity-100', 'opacity-0');
    }, 4000);
  }
}
```

- [ ] **Step 5: Build and verify**

```bash
cd web && npm run build
```

Build should succeed.

- [ ] **Step 6: Commit**

```bash
git add web/src/types.ts web/src/state.ts web/src/components/Settings.ts web/src/components/Toast.ts
git commit -m "feat(desktop): types, event bus, settings drawer, toast"
```

---

## Task 5: JS bridge wrapper + main wiring

**Files:**
- Create: `web/src/bridge.ts`
- Modify: `web/src/main.ts`

- [ ] **Step 1: Create `web/src/bridge.ts`**

```ts
import { bus } from './state';
import type { AppConfig, VAEvent } from './types';

declare global {
  interface Window {
    pywebview: {
      api: {
        start_listening(): Promise<void>;
        stop_listening():  Promise<void>;
        send_text(text: string): Promise<void>;
        get_config(): Promise<AppConfig>;
        save_config(cfg: AppConfig & { _secret?: string }): Promise<{ok: boolean; errors?: string[]}>;
        quit(): Promise<void>;
      };
    };
    va: {
      emit(event: VAEvent): void;
    };
  }
}

// Python pushes events here: window.va.emit(...).
window.va = {
  emit: (event: VAEvent) => bus.emit(event),
};

const hasPy = (): boolean => typeof window !== 'undefined' && typeof window.pywebview !== 'undefined';

export const bridge = {
  startListening: async () => hasPy() ? window.pywebview.api.start_listening() : void 0,
  stopListening:  async () => hasPy() ? window.pywebview.api.stop_listening()  : void 0,
  sendText:       async (text: string) => hasPy() ? window.pywebview.api.send_text(text) : void 0,
  getConfig:      async (): Promise<AppConfig> => hasPy()
    ? window.pywebview.api.get_config()
    : ({ provider: 'anthropic', model: 'claude-sonnet-4-6', hotkey: 'ctrl+shift+space', allowed_roots: ['~'], ollama_base_url: null } as AppConfig),
  saveConfig:     async (cfg: AppConfig & { _secret?: string }) => hasPy()
    ? window.pywebview.api.save_config(cfg)
    : ({ ok: true } as const),
  quit:           async () => hasPy() ? window.pywebview.api.quit() : void 0,
};

// Tell Python that the page is ready, in case it wants to push an initial config.
if (hasPy()) {
  // pywebview readiness — pywebviewready DOM event fires when window.pywebview is injected
  document.addEventListener('pywebviewready', () => {
    void bridge.getConfig().then((cfg) => bus.emit({ type: 'config', cfg }));
  });
} else {
  // Browser dev: push a fake config after a tick.
  setTimeout(async () => {
    const cfg = await bridge.getConfig();
    bus.emit({ type: 'config', cfg });
  }, 100);
}
```

- [ ] **Step 2: Replace `web/src/main.ts`** to wire everything via the bus

```ts
import './style.css';
import { Header } from './components/Header';
import { Orb }    from './components/Orb';
import { Transcript } from './components/Transcript';
import { Composer } from './components/Composer';
import { Settings } from './components/Settings';
import { Toast } from './components/Toast';
import { bus } from './state';
import { bridge } from './bridge';
import type { AppConfig } from './types';

const root = document.getElementById('app')!;
root.className = 'h-screen flex flex-col';
root.innerHTML = '';

const header     = new Header(root);
const orb        = new Orb(root);
const transcript = new Transcript(root);
const composer   = new Composer(root);
const settings   = new Settings(document.body);
const toast      = new Toast(document.body);

// Constrain transcript so the orb keeps the visual lead
const transcriptEl = root.children[2] as HTMLElement;
transcriptEl.classList.remove('flex-1');
transcriptEl.classList.add('max-h-48', 'shrink-0');

let currentConfig: AppConfig | null = null;

bus.on((e) => {
  switch (e.type) {
    case 'status':
      header.setStatus(e.value);
      orb.setState(e.value);
      break;
    case 'transcript':
      transcript.push({ speaker: e.speaker, text: e.text, tool_call: e.tool_call });
      break;
    case 'audio_level':
      orb.setRms(e.rms);
      break;
    case 'config':
      currentConfig = e.cfg;
      break;
    case 'toast':
      toast.show(e.level, e.message);
      break;
  }
});

composer.onSubmit((text) => { void bridge.sendText(text); });
composer.onRecord(() => { void bridge.startListening(); });
header.onSettingsClick(() => { if (currentConfig) settings.open(currentConfig); });
settings.onSave(async (cfg) => bridge.saveConfig(cfg as AppConfig));

// Keyboard shortcuts: Esc closes settings; Cmd/Ctrl+, opens.
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') settings.close();
  if ((e.metaKey || e.ctrlKey) && e.key === ',') {
    e.preventDefault();
    if (currentConfig) settings.open(currentConfig);
  }
});
```

- [ ] **Step 3: Build and dev-test**

```bash
cd web && npm run build && npm run dev
```

Open http://localhost:5173. Browser-only: orb should pulse, settings opens with default values, save closes the drawer with a fake `{ok: true}`. Stop dev server.

- [ ] **Step 4: Commit**

```bash
git add web/src/bridge.ts web/src/main.ts
git commit -m "feat(desktop): JS bridge wrapper and main wiring"
```

---

## Task 6: Python `desktop` module — Bridge contract (TDD)

**Files:**
- Create: `src/voice_assistant/desktop/__init__.py`
- Create: `src/voice_assistant/desktop/bridge.py`
- Create: `src/voice_assistant/desktop/events.py`
- Create: `tests/test_desktop_bridge.py`
- Create: `tests/test_desktop_events.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add the `desktop` extra to `pyproject.toml`**

Find `[project.optional-dependencies]` and add:

```toml
desktop = ["pywebview>=5"]
```

Find `[tool.setuptools.packages.find]` and below it add:

```toml
[tool.setuptools.package-data]
voice_assistant = ["desktop/web_dist/**/*"]
```

- [ ] **Step 2: Failing tests for the events module**

Create `tests/test_desktop_events.py`:

```python
import time
from voice_assistant.desktop.events import EventBus


def test_bus_delivers_events_to_subscriber():
    bus = EventBus()
    seen = []
    bus.subscribe(lambda e: seen.append(e))
    bus.publish({"type": "status", "value": "idle"})
    assert seen == [{"type": "status", "value": "idle"}]


def test_audio_level_is_throttled_to_30hz():
    bus = EventBus()
    seen = []
    bus.subscribe(lambda e: seen.append(e))
    # Send 100 audio_level events tightly — only ~3 should pass through within 100ms.
    for i in range(100):
        bus.publish({"type": "audio_level", "rms": i / 100})
    # Allow the throttle window to admit at most ceil(0.1s * 30Hz) + 1 = 4 events.
    # Events emitted within the same millisecond are coalesced to one.
    assert 1 <= len(seen) <= 5, f"throttling broken: {len(seen)} delivered"


def test_audio_level_throttle_releases_over_time():
    bus = EventBus()
    seen = []
    bus.subscribe(lambda e: seen.append(e))
    bus.publish({"type": "audio_level", "rms": 0.1})
    time.sleep(0.05)  # > 1/30s
    bus.publish({"type": "audio_level", "rms": 0.2})
    assert len(seen) == 2


def test_other_event_types_are_not_throttled():
    bus = EventBus()
    seen = []
    bus.subscribe(lambda e: seen.append(e))
    for i in range(10):
        bus.publish({"type": "status", "value": "idle"})
    assert len(seen) == 10
```

- [ ] **Step 3: Run failing tests**

```bash
.venv/bin/pytest tests/test_desktop_events.py -v
```

Expected: 4 ImportError failures.

- [ ] **Step 4: Implement `events.py`**

Create `src/voice_assistant/desktop/__init__.py` (empty file) and `src/voice_assistant/desktop/events.py`:

```python
from __future__ import annotations
import time
from collections.abc import Callable
from typing import Any


class EventBus:
    """Pub-sub bus with per-event-type throttling.

    Used between the orchestrator/audio threads (publishers) and the
    PyWebView GUI thread (subscriber that pushes to JS).
    """

    _AUDIO_LEVEL_INTERVAL_S = 1 / 30  # 30 Hz

    def __init__(self) -> None:
        self._subscribers: list[Callable[[dict[str, Any]], None]] = []
        self._last_audio_level_at: float = 0.0

    def subscribe(self, fn: Callable[[dict[str, Any]], None]) -> Callable[[], None]:
        self._subscribers.append(fn)

        def _unsub() -> None:
            try:
                self._subscribers.remove(fn)
            except ValueError:
                pass

        return _unsub

    def publish(self, event: dict[str, Any]) -> None:
        if event.get("type") == "audio_level":
            now = time.monotonic()
            if now - self._last_audio_level_at < self._AUDIO_LEVEL_INTERVAL_S:
                return
            self._last_audio_level_at = now
        for fn in list(self._subscribers):
            try:
                fn(event)
            except Exception:  # subscriber failure must not crash the bus
                pass
```

- [ ] **Step 5: Run tests; should pass**

```bash
.venv/bin/pytest tests/test_desktop_events.py -v
```

Expected: 4 passing.

- [ ] **Step 6: Failing tests for the Bridge**

Create `tests/test_desktop_bridge.py`:

```python
from __future__ import annotations
from pathlib import Path
import os
import pytest
from voice_assistant.desktop.bridge import Bridge
from voice_assistant.desktop.events import EventBus


@pytest.fixture
def tmp_paths(tmp_path):
    return tmp_path / "config.yaml", tmp_path / ".env"


@pytest.fixture
def bridge_with_config(tmp_paths):
    cfg_path, env_path = tmp_paths
    bus = EventBus()
    sent: list[str] = []
    bridge = Bridge(
        config_path=cfg_path,
        env_path=env_path,
        bus=bus,
        on_send_text=lambda t: sent.append(t),
        on_listening_start=lambda: None,
        on_listening_stop=lambda: None,
    )
    return bridge, bus, sent, cfg_path, env_path


def test_bridge_send_text_invokes_callback(bridge_with_config):
    bridge, _, sent, _, _ = bridge_with_config
    bridge.send_text("hello")
    assert sent == ["hello"]


def test_bridge_get_config_returns_default_shape_when_missing(bridge_with_config):
    bridge, _, _, _, _ = bridge_with_config
    cfg = bridge.get_config()
    assert cfg["provider"] in ("anthropic", "openai", "gemini", "ollama")
    assert isinstance(cfg["model"], str) and cfg["model"]
    assert isinstance(cfg["hotkey"], str)
    assert isinstance(cfg["allowed_roots"], list)


def test_bridge_save_config_writes_files_and_strips_stale_keys(bridge_with_config):
    bridge, _, _, cfg_path, env_path = bridge_with_config
    env_path.write_text("ANTHROPIC_API_KEY=old\nFOO=bar\n")
    result = bridge.save_config({
        "provider": "openai",
        "model": "gpt-4o",
        "hotkey": "ctrl+shift+space",
        "allowed_roots": ["~"],
        "ollama_base_url": None,
        "_secret": "sk-new",
    })
    assert result == {"ok": True}
    assert cfg_path.exists()
    env_text = env_path.read_text()
    assert "OPENAI_API_KEY=sk-new" in env_text
    assert "ANTHROPIC_API_KEY" not in env_text
    assert "FOO=bar" in env_text


def test_bridge_save_config_validation_failure_returns_errors(bridge_with_config):
    bridge, _, _, cfg_path, _ = bridge_with_config
    result = bridge.save_config({
        "provider": "nonexistent",
        "model": "x",
        "hotkey": "x",
        "allowed_roots": ["~"],
        "ollama_base_url": None,
        "_secret": "k",
    })
    assert result["ok"] is False
    assert isinstance(result["errors"], list) and result["errors"]
    assert not cfg_path.exists()


def test_bridge_save_config_emits_config_event(bridge_with_config):
    bridge, bus, _, _, _ = bridge_with_config
    seen: list[dict] = []
    bus.subscribe(lambda e: seen.append(e) if e.get("type") == "config" else None)
    bridge.save_config({
        "provider": "anthropic",
        "model": "claude-sonnet-4-6",
        "hotkey": "ctrl+shift+space",
        "allowed_roots": ["~"],
        "ollama_base_url": None,
        "_secret": "sk-ant-test",
    })
    assert len(seen) == 1
    assert seen[0]["cfg"]["provider"] == "anthropic"


def test_bridge_env_file_is_mode_0600(bridge_with_config):
    if os.name == "nt":
        pytest.skip("file modes are POSIX-only")
    bridge, _, _, _, env_path = bridge_with_config
    bridge.save_config({
        "provider": "anthropic",
        "model": "claude-sonnet-4-6",
        "hotkey": "ctrl+shift+space",
        "allowed_roots": ["~"],
        "ollama_base_url": None,
        "_secret": "sk-ant-test",
    })
    assert oct(env_path.stat().st_mode & 0o777) == "0o600"
```

- [ ] **Step 7: Implement `bridge.py`**

Create `src/voice_assistant/desktop/bridge.py`:

```python
from __future__ import annotations
from collections.abc import Callable
from pathlib import Path
from typing import Any
import yaml
from voice_assistant.config import Config
from voice_assistant.setup_wizard import (
    DEFAULT_MODELS, WizardAnswers, render_config, render_env, PROVIDER_ENV_VAR,
)
from voice_assistant.desktop.events import EventBus


def _config_to_dict(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        raw = yaml.safe_load(path.read_text())
        cfg = Config.model_validate(raw)
    except Exception:
        return None
    return {
        "provider": cfg.brain.provider,
        "model":    cfg.brain.model,
        "hotkey":   cfg.audio.hotkey,
        "allowed_roots": [str(p) for p in cfg.safety.allowed_roots],
        "ollama_base_url": None,
    }


def _default_config_dict() -> dict[str, Any]:
    return {
        "provider": "anthropic",
        "model":    DEFAULT_MODELS["anthropic"],
        "hotkey":   "ctrl+shift+space",
        "allowed_roots": ["~"],
        "ollama_base_url": None,
    }


class Bridge:
    """JS-callable surface. All methods MUST be JSON-safe in/out."""

    def __init__(
        self,
        *,
        config_path: Path,
        env_path: Path,
        bus: EventBus,
        on_send_text: Callable[[str], None],
        on_listening_start: Callable[[], None],
        on_listening_stop: Callable[[], None],
    ) -> None:
        self._config_path = config_path
        self._env_path = env_path
        self._bus = bus
        self._on_send_text = on_send_text
        self._on_listening_start = on_listening_start
        self._on_listening_stop = on_listening_stop

    # ---- methods JS calls --------------------------------------------------
    def start_listening(self) -> None:
        self._on_listening_start()

    def stop_listening(self) -> None:
        self._on_listening_stop()

    def send_text(self, text: str) -> None:
        self._on_send_text(text)

    def get_config(self) -> dict[str, Any]:
        return _config_to_dict(self._config_path) or _default_config_dict()

    def save_config(self, cfg: dict[str, Any]) -> dict[str, Any]:
        try:
            provider = cfg["provider"]
            if provider not in PROVIDER_ENV_VAR:
                raise ValueError(f"unknown provider: {provider!r}")
            roots = [Path(p) for p in (cfg.get("allowed_roots") or ["~"])]
            answers = WizardAnswers(
                provider=provider,
                model=cfg["model"],
                hotkey=cfg["hotkey"],
                allowed_roots=roots,
                ollama_base_url=cfg.get("ollama_base_url"),
            )
            yaml_text = render_config(answers)
            Config.model_validate(yaml.safe_load(yaml_text))  # validation
        except Exception as exc:
            return {"ok": False, "errors": [str(exc)]}

        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._env_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(yaml_text)

        secret = cfg.get("_secret")
        if not secret and provider == "ollama":
            secret = cfg.get("ollama_base_url") or "http://localhost:11434"
        if secret:
            existing = self._env_path.read_text() if self._env_path.exists() else ""
            self._env_path.write_text(render_env(provider, secret, existing=existing))
            try:
                self._env_path.chmod(0o600)
            except OSError:
                pass

        # Emit fresh config event so the UI re-renders.
        self._bus.publish({"type": "config", "cfg": _config_to_dict(self._config_path) or _default_config_dict()})
        return {"ok": True}

    def quit(self) -> None:
        # Window close is handled in window.py; this is a hook for the JS quit shortcut.
        pass
```

- [ ] **Step 8: Run all desktop tests**

```bash
.venv/bin/pytest tests/test_desktop_bridge.py tests/test_desktop_events.py -v
```

Expected: 10 passing.

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml src/voice_assistant/desktop/ tests/test_desktop_bridge.py tests/test_desktop_events.py
git commit -m "feat(desktop): Bridge contract + EventBus with throttled audio_level"
```

---

## Task 7: PyWebView window factory + JS-event push helper

**Files:**
- Create: `src/voice_assistant/desktop/window.py`

- [ ] **Step 1: Create `src/voice_assistant/desktop/window.py`**

```python
from __future__ import annotations
import json
import logging
import threading
from importlib import resources
from pathlib import Path
from typing import Callable, Any

from voice_assistant.desktop.bridge import Bridge
from voice_assistant.desktop.events import EventBus

log = logging.getLogger(__name__)


def _resolve_index_html() -> str:
    """Locate the bundled web_dist/index.html via importlib.resources."""
    try:
        files = resources.files("voice_assistant") / "desktop" / "web_dist"
        index = files / "index.html"
        return str(index)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        raise RuntimeError(
            "voice-assistant desktop frontend bundle missing — please reinstall "
            "with the [desktop] extra and ensure web/dist was built before packaging."
        ) from e


class DesktopApp:
    """Opens the PyWebView window and pumps EventBus events into the page."""

    def __init__(
        self,
        *,
        bridge: Bridge,
        bus: EventBus,
        title: str = "voice-assistant",
        width: int = 800,
        height: int = 720,
    ) -> None:
        self._bridge = bridge
        self._bus = bus
        self._title = title
        self._width = width
        self._height = height
        self._window: Any | None = None
        self._unsubscribe: Callable[[], None] | None = None

    def run(self) -> None:
        try:
            import webview  # PyWebView
        except ImportError as e:
            raise RuntimeError(
                "PyWebView not installed. Run: pip install voice-assistant[desktop]"
            ) from e

        index_path = _resolve_index_html()
        self._window = webview.create_window(
            title=self._title,
            url=f"file://{index_path}",
            js_api=self._bridge,
            width=self._width,
            height=self._height,
            min_size=(720, 600),
            background_color="#0b0d10",
        )

        def _on_loaded() -> None:
            # Subscribe to the bus once the window is ready.
            self._unsubscribe = self._bus.subscribe(self._push_to_js)
            # Publish initial config so the UI populates.
            self._bus.publish({"type": "config", "cfg": self._bridge.get_config()})
            self._bus.publish({"type": "status", "value": "idle"})

        self._window.events.loaded += _on_loaded

        # Run the GUI event loop on the calling thread (must be the main thread on macOS).
        webview.start(debug=False)

        # Cleanup
        if self._unsubscribe:
            self._unsubscribe()

    def _push_to_js(self, event: dict[str, Any]) -> None:
        """Marshal an event to JS via window.va.emit().

        Called from the publisher's thread; PyWebView's evaluate_js is thread-safe.
        """
        if self._window is None:
            return
        try:
            payload = json.dumps(event)
            self._window.evaluate_js(f"window.va && window.va.emit({payload})")
        except Exception:
            log.exception("failed to push event to JS")
```

- [ ] **Step 2: Verify the module imports cleanly**

```bash
.venv/bin/python -c "from voice_assistant.desktop.window import DesktopApp; print('ok')"
```

Expected: `ok` (no PyWebView import yet because `DesktopApp.run` defers the import).

- [ ] **Step 3: Commit**

```bash
git add src/voice_assistant/desktop/window.py
git commit -m "feat(desktop): PyWebView window factory + event push to JS"
```

---

## Task 8: CLI `--gui` / `--no-gui` flags + auto-detect + dispatch

**Files:**
- Modify: `src/voice_assistant/cli.py`
- Modify: `src/voice_assistant/app.py`
- Modify: `tests/test_app_text_mode.py` (verify --gui doesn't break text mode tests)

- [ ] **Step 1: Add a tiny test that confirms `--no-gui` keeps text mode working**

Append to `tests/test_app_text_mode.py`:

```python
def test_no_gui_flag_runs_text_mode(monkeypatch, tmp_path):
    """`--no-gui --text` must not regress text mode dispatch."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("""
brain: { provider: anthropic, model: claude-sonnet-4-6 }
stt:   { engine: faster-whisper, model: small, language: en }
tts:   { engine: piper, voice: en_US-amy-medium }
audio: { trigger: hotkey, hotkey: ctrl+shift+space, silence_seconds: 1.5 }
safety: { allowed_roots: ["~"], destructive_requires_confirmation: true, delete_rate_per_minute: 5 }
logging: { level: INFO, file: /tmp/x.log }
""")
    monkeypatch.setattr("sys.argv", ["voice-assistant", "--config", str(config_path), "--no-gui", "--text"])
    monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(EOFError()))
    from voice_assistant.cli import main
    main()  # exits cleanly on EOF
```

- [ ] **Step 2: Run; expect failure**

```bash
.venv/bin/pytest tests/test_app_text_mode.py::test_no_gui_flag_runs_text_mode -v
```

Expected: argparse error about unrecognised `--no-gui`.

- [ ] **Step 3: Modify `src/voice_assistant/cli.py`** to add the flags + dispatch

Replace the `argparse` block and the post-parse logic in `main()`. Keep all existing logic intact except where indicated.

```python
def main() -> None:
    parser = argparse.ArgumentParser(prog="voice-assistant")
    parser.add_argument(
        "--config", type=Path, default=Path("config.yaml"),
        help="Path to config file (default: ./config.yaml)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--text",   action="store_true", help="Text mode (no audio).")
    mode.add_argument("--setup",  action="store_true", help="Run interactive setup wizard.")
    mode.add_argument("--gui",    action="store_true", help="Force desktop window mode.")
    mode.add_argument("--no-gui", action="store_true", help="Force CLI mode even with a display.", dest="no_gui")
    parser.add_argument(
        "--force", action="store_true",
        help="With --setup: overwrite an existing config without prompting.",
    )
    args = parser.parse_args()

    if args.setup:
        from pathlib import Path as _P
        from voice_assistant.setup_wizard import run_wizard
        home = _P.home() / ".voice-assistant"
        run_wizard(
            config_path=home / "config.yaml",
            env_path=home / ".env",
            force=args.force,
        )
        return

    load_dotenv()
    cfg = load_config(args.config)
    configure_logging(level=cfg.logging.level, log_file=cfg.logging.file)

    # Build orchestrator (existing code unchanged) ...
    policy = SafetyPolicy(
        allowed_roots=cfg.safety.allowed_roots,
        destructive_requires_confirmation=cfg.safety.destructive_requires_confirmation,
        delete_rate_per_minute=cfg.safety.delete_rate_per_minute,
    )
    brain = Brain(provider=cfg.brain.provider, model=cfg.brain.model)
    gmail_creds = None
    if cfg.gmail:
        if cfg.gmail.credentials_file.exists():
            gmail_creds = cfg.gmail.credentials_file
        else:
            log.warning(
                "gmail credentials_file %s not found; send_email tool disabled",
                cfg.gmail.credentials_file,
            )
    orch = Orchestrator(
        brain=brain,
        tools=build_registry(policy=policy, gmail_credentials_file=gmail_creds),
    )

    # Mode resolution
    if args.text:
        _run_text_mode(orch)
        return
    if args.no_gui:
        _run_text_mode(orch)
        return
    if args.gui or _gui_available():
        try:
            _run_gui_mode(orch, cfg, args.config)
            return
        except Exception as exc:
            log.warning("GUI mode failed (%s); falling back to voice CLI", exc)
    _run_voice_mode(orch, cfg)


def _gui_available() -> bool:
    """Heuristic: do we have a graphical session AND PyWebView AND the bundle?"""
    import os, sys
    if os.environ.get("VA_NO_GUI"):
        return False
    if sys.platform.startswith("linux"):
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return False
    try:
        import webview  # noqa: F401
    except ImportError:
        return False
    try:
        from voice_assistant.desktop.window import _resolve_index_html
        _resolve_index_html()
    except Exception:
        return False
    return True


def _run_gui_mode(orch, cfg, config_path: Path) -> None:
    from pathlib import Path as _P
    from voice_assistant.desktop.bridge import Bridge
    from voice_assistant.desktop.events import EventBus
    from voice_assistant.desktop.window import DesktopApp

    bus = EventBus()
    home = _P.home() / ".voice-assistant"

    def _on_text(text: str) -> None:
        bus.publish({"type": "transcript", "speaker": "user", "text": text})
        bus.publish({"type": "status", "value": "thinking"})
        try:
            reply = orch.handle(text)
            bus.publish({"type": "transcript", "speaker": "assistant", "text": reply})
        except Exception as exc:
            log.exception("orch.handle failed")
            bus.publish({"type": "toast", "level": "error", "message": str(exc)})
        finally:
            bus.publish({"type": "status", "value": "idle"})

    bridge = Bridge(
        config_path=home / "config.yaml",
        env_path=home / ".env",
        bus=bus,
        on_send_text=lambda t: threading.Thread(target=_on_text, args=(t,), daemon=True).start(),
        on_listening_start=lambda: bus.publish({"type": "toast", "level": "info", "message": "Voice mode comes online in Task 9"}),
        on_listening_stop=lambda: None,
    )
    DesktopApp(bridge=bridge, bus=bus).run()


def _run_text_mode(orch) -> None:
    print("voice-assistant text mode. Ctrl-D to exit.")
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            print()
            return
        except KeyboardInterrupt:
            print()
            return
        if not line:
            continue
        try:
            print(orch.handle(line))
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log.exception("error in handle")
            print(f"[error: {e}]")


def _run_voice_mode(orch, cfg) -> None:
    from voice_assistant.audio_input import HotkeyListener, record_until_silence
    from voice_assistant.stt import Transcriber
    from voice_assistant.tts import Speaker

    if cfg.audio.trigger != "hotkey":
        raise SystemExit(
            f"audio.trigger='{cfg.audio.trigger}' is not implemented in this build. "
            "Set audio.trigger=hotkey in config.yaml."
        )
    listener = HotkeyListener(cfg.audio.hotkey)
    transcriber = Transcriber(model_name=cfg.stt.model, language=cfg.stt.language)
    speaker = Speaker(voice=cfg.tts.voice)

    print(f"voice-assistant ready. Press {cfg.audio.hotkey} to talk.")
    while True:
        try:
            listener.wait_for_press()
        except KeyboardInterrupt:
            print()
            return
        print("listening...")
        try:
            audio = record_until_silence(silence_seconds=cfg.audio.silence_seconds)
            text = transcriber.transcribe(audio).strip()
            if not text:
                print("(nothing heard)")
                continue
            print(f"you: {text}")
            reply = orch.handle(text)
            print(f"assistant: {reply}")
            speaker.speak(reply)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log.exception("error in audio loop")
            print(f"[error: {e}]")
```

Add `import threading` at the top of the file alongside other stdlib imports.

- [ ] **Step 4: Run all tests**

```bash
.venv/bin/pytest -q
```

Expected: all 107+ existing + new bridge/events tests pass; the new `test_no_gui_flag_runs_text_mode` passes.

- [ ] **Step 5: Commit**

```bash
git add src/voice_assistant/cli.py tests/test_app_text_mode.py
git commit -m "feat(cli): --gui / --no-gui flags with auto-detect + GUI dispatch"
```

---

## Task 9: Wire voice + TTS into GUI mode

**Files:**
- Modify: `src/voice_assistant/cli.py` (the `_run_gui_mode` function)

- [ ] **Step 1: Replace `_run_gui_mode` in `cli.py`** with the full integration

```python
def _run_gui_mode(orch, cfg, config_path: Path) -> None:
    """GUI runtime: hotkey + audio + STT + orch + TTS, all event-driven."""
    from pathlib import Path as _P
    from voice_assistant.desktop.bridge import Bridge
    from voice_assistant.desktop.events import EventBus
    from voice_assistant.desktop.window import DesktopApp
    from voice_assistant.audio_input import HotkeyListener, record_until_silence
    from voice_assistant.stt import Transcriber
    from voice_assistant.tts import Speaker

    bus = EventBus()
    home = _P.home() / ".voice-assistant"

    transcriber: Transcriber | None = None
    speaker: Speaker | None = None
    listener: HotkeyListener | None = None
    if cfg.audio.trigger == "hotkey":
        try:
            transcriber = Transcriber(model_name=cfg.stt.model, language=cfg.stt.language)
            speaker     = Speaker(voice=cfg.tts.voice)
            listener    = HotkeyListener(cfg.audio.hotkey)
        except Exception as exc:
            log.warning("audio init failed (%s); voice mode disabled", exc)

    def _do_request(text: str) -> None:
        bus.publish({"type": "transcript", "speaker": "user", "text": text})
        bus.publish({"type": "status", "value": "thinking"})
        try:
            reply = orch.handle(text)
            bus.publish({"type": "transcript", "speaker": "assistant", "text": reply})
            if speaker is not None:
                bus.publish({"type": "status", "value": "speaking"})
                try:
                    speaker.speak(reply)
                except Exception as exc:
                    log.exception("speaker.speak failed")
                    bus.publish({"type": "toast", "level": "warn", "message": f"TTS failed: {exc}"})
        except Exception as exc:
            log.exception("orch.handle failed")
            bus.publish({"type": "toast", "level": "error", "message": str(exc)})
            bus.publish({"type": "status", "value": "error"})
        finally:
            bus.publish({"type": "status", "value": "idle"})

    def _record_and_run() -> None:
        if transcriber is None:
            bus.publish({"type": "toast", "level": "warn", "message": "Voice not available — type instead."})
            return
        bus.publish({"type": "status", "value": "listening"})
        try:
            audio = record_until_silence(
                silence_seconds=cfg.audio.silence_seconds,
                level_callback=lambda rms: bus.publish({"type": "audio_level", "rms": float(rms)}),
            )
            text = transcriber.transcribe(audio).strip()
            if not text:
                bus.publish({"type": "toast", "level": "info", "message": "Nothing heard."})
                bus.publish({"type": "status", "value": "idle"})
                return
            _do_request(text)
        except Exception as exc:
            log.exception("voice path failed")
            bus.publish({"type": "toast", "level": "error", "message": str(exc)})
            bus.publish({"type": "status", "value": "idle"})

    def _on_text(text: str) -> None:
        threading.Thread(target=_do_request, args=(text,), daemon=True).start()

    def _on_listen_start() -> None:
        threading.Thread(target=_record_and_run, daemon=True).start()

    bridge = Bridge(
        config_path=home / "config.yaml",
        env_path=home / ".env",
        bus=bus,
        on_send_text=_on_text,
        on_listening_start=_on_listen_start,
        on_listening_stop=lambda: None,
    )

    # System-wide hotkey worker thread.
    def _hotkey_worker() -> None:
        if listener is None:
            return
        while True:
            try:
                listener.wait_for_press()
            except Exception:
                break
            _on_listen_start()

    if listener is not None:
        threading.Thread(target=_hotkey_worker, daemon=True).start()

    DesktopApp(bridge=bridge, bus=bus).run()
```

- [ ] **Step 2: Add `level_callback` to `record_until_silence` (if not already present)**

If `audio_input.record_until_silence` doesn't accept `level_callback`, add it as a keyword-only parameter that's invoked once per chunk with the current RMS value. Open `src/voice_assistant/audio_input.py`, find `record_until_silence`, and add:

```python
def record_until_silence(
    *,
    silence_seconds: float,
    level_callback: Callable[[float], None] | None = None,
    # ... existing params
) -> bytes:
    # ... existing code, then where each audio chunk is read:
    if level_callback is not None:
        rms = float((chunk_array.astype("float32") ** 2).mean() ** 0.5) / 32768.0
        level_callback(rms)
    # ... existing silence-detection code
```

(If you find `record_until_silence` doesn't have a chunked loop, this step becomes a small refactor — split the existing recording loop into chunks and call back per chunk. Keep the public signature backwards-compatible by making `level_callback` optional.)

Run `pytest tests/test_audio_input.py -v` afterwards to confirm existing audio tests still pass. If they were mocking the old signature, update the mocks to match the new keyword-only param.

- [ ] **Step 3: Smoke test (manual; no automated test for the GUI integration)**

```bash
.venv/bin/python -m voice_assistant --gui
```

Expected: window opens (if PyWebView and the bundle are available); typing a command in the composer routes through orchestrator and shows the response in the transcript. Pressing the hotkey shows "Voice not available" toast unless audio prereqs are present.

- [ ] **Step 4: Commit**

```bash
git add src/voice_assistant/cli.py src/voice_assistant/audio_input.py
git commit -m "feat(desktop): wire voice + TTS into GUI mode (hotkey, audio level, status events)"
```

---

## Task 10: Build pipeline — copy web/dist into the package

**Files:**
- Create: `scripts/copy-web-dist.mjs`
- Modify: `pyproject.toml` (already has package_data; verify path)
- Modify: `MANIFEST.in` (create if missing)
- Modify: `web/package.json` (add `postbuild` to copy into the package)

- [ ] **Step 1: Create `scripts/copy-web-dist.mjs`**

```js
import { cpSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, '..');
const src = join(repoRoot, 'web', 'dist');
const dst = join(repoRoot, 'src', 'voice_assistant', 'desktop', 'web_dist');

if (!existsSync(src)) {
  console.error(`copy-web-dist: source ${src} does not exist; run 'cd web && npm run build' first.`);
  process.exit(1);
}

if (existsSync(dst)) rmSync(dst, { recursive: true, force: true });
mkdirSync(dst, { recursive: true });
cpSync(src, dst, { recursive: true });
console.log(`copied ${src} → ${dst}`);
```

- [ ] **Step 2: Modify `web/package.json`** to run the copy after build

Edit the `scripts` block:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build && node ../scripts/copy-web-dist.mjs",
    "preview": "vite preview"
  }
}
```

- [ ] **Step 3: Create or modify root `MANIFEST.in`** so sdist includes the bundle

```
recursive-include src/voice_assistant/desktop/web_dist *
```

- [ ] **Step 4: Add `web_dist/` to root `.gitignore`**

Append to `.gitignore`:

```
src/voice_assistant/desktop/web_dist/
web/dist/
```

(The bundle is generated; we don't track it in git. The install scripts trigger `npm run build` first if needed; for end-user `pip install ... @ git+...`, we add a build hook in the next step.)

- [ ] **Step 5: Add a build-time guard so `pip install` builds the frontend automatically**

Modify `pyproject.toml` `[build-system]`:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"
```

(That's already the value; no change needed.)

For users installing from a git clone (the `pip install ... @ git+...` path), pip downloads the source then runs `python -m build`. That step doesn't run npm. Two options:

A. Document the requirement: source installs need `cd web && npm run build` first. The desktop extra is *not* available without it.

B. Pre-build the bundle in CI on tagged releases, ship as part of the source tarball. (Out of scope.)

For this task, take option **A**: in `_resolve_index_html`, if the bundle is missing, return a clear error pointing the user at `npm run build`. The auto-detect already drops to CLI in that case.

- [ ] **Step 6: Build the bundle locally and verify packaging**

```bash
cd web && npm run build
ls -la /home/zeeshan-ahmed/voice-assistant/src/voice_assistant/desktop/web_dist/
```

Expected: `web_dist/index.html` plus an `assets/` folder. `_resolve_index_html()` must succeed.

- [ ] **Step 7: Verify the GUI flag works end-to-end**

```bash
.venv/bin/python -c "
import sys
sys.argv = ['voice-assistant', '--gui']
from voice_assistant.cli import main
print('would call main() with --gui — skipping GUI launch in CI')
"
```

(Manual: actually run `voice-assistant --gui` if you have a graphical session. Window should open.)

- [ ] **Step 8: Commit**

```bash
git add scripts/copy-web-dist.mjs MANIFEST.in web/package.json .gitignore
git commit -m "build(desktop): postbuild copy of web/dist into package_data"
```

---

## Task 11: Install-script integration

**Files:**
- Modify: `scripts/install.sh`
- Modify: `scripts/install.ps1`

- [ ] **Step 1: Modify `scripts/install.sh`** — add the desktop extra and the GTK warning

Find the line:

```bash
"$VA_HOME/.venv/bin/pip" install "voice-assistant[audio,gmail] @ git+$REPO_URL"
```

Change to:

```bash
EXTRAS="audio,gmail"
if [ -z "${VA_NO_DESKTOP:-}" ]; then EXTRAS="$EXTRAS,desktop"; fi
"$VA_HOME/.venv/bin/pip" install "voice-assistant[$EXTRAS] @ git+$REPO_URL"
```

In the Linux audio-prereq block, after the espeak-ng check, add a desktop-prereq check:

```bash
  if [ -z "${VA_NO_DESKTOP:-}" ]; then
    # PyWebView on Linux needs WebKit2GTK + GTK3.
    if ! pkg-config --exists webkit2gtk-4.1 2>/dev/null \
       && ! pkg-config --exists webkit2gtk-4.0 2>/dev/null; then
      if   command -v apt-get >/dev/null; then warn "Desktop window needs WebKit2GTK + GTK3. Run: sudo apt-get install -y python3-gi gir1.2-webkit2-4.1 libgtk-3-0"
      elif command -v dnf     >/dev/null; then warn "Desktop window needs WebKit2GTK + GTK3. Run: sudo dnf install -y python3-gobject webkit2gtk4.1 gtk3"
      elif command -v pacman  >/dev/null; then warn "Desktop window needs WebKit2GTK + GTK3. Run: sudo pacman -S --needed python-gobject webkit2gtk-4.1 gtk3"
      fi
      warn "GUI may not start; CLI fallback is automatic. Set VA_NO_DESKTOP=1 to skip."
    fi
  fi
```

- [ ] **Step 2: Modify `scripts/install.ps1`** — add the desktop extra

Find the line:

```powershell
& $pip install "voice-assistant[audio,gmail] @ git+$RepoUrl"
```

Change to:

```powershell
$Extras = if ($env:VA_NO_DESKTOP -eq '1') { 'audio,gmail' } else { 'audio,gmail,desktop' }
& $pip install "voice-assistant[$Extras] @ git+$RepoUrl"
```

- [ ] **Step 3: Run shellcheck if available**

```bash
shellcheck scripts/install.sh || echo "shellcheck not installed; skipping"
```

- [ ] **Step 4: Smoke-test the local install path (no curl)**

```bash
rm -rf ~/.local/share/voice-assistant ~/.local/bin/voice-assistant
bash /home/zeeshan-ahmed/voice-assistant/scripts/install.sh --no-setup 2>&1 | tail -20
```

Expected: install completes, the line `installing voice-assistant from $REPO_URL` includes `[audio,gmail,desktop]`. PyWebView appears in the installed packages list.

- [ ] **Step 5: Commit**

```bash
git add scripts/install.sh scripts/install.ps1
git commit -m "feat(install): add desktop extra to install scripts (skippable via VA_NO_DESKTOP)"
```

---

## Task 12: Final verification + push

**Files:** none (verification only)

- [ ] **Step 1: Full test suite**

```bash
.venv/bin/pytest -q
```

Expected: all tests pass (~107 existing + 11 desktop bridge/events + 1 no-gui = ~119).

- [ ] **Step 2: Frontend build clean**

```bash
cd web && npm run build
```

Expected: `dist/` rebuilt and copied to `src/voice_assistant/desktop/web_dist/`.

- [ ] **Step 3: Smoke desktop launch (skip if no display)**

If a graphical session is available:

```bash
.venv/bin/python -m voice_assistant --gui
```

Click around: orb pulses, settings opens, type a command, see response. Close the window — process exits.

If no display, confirm graceful CLI fallback:

```bash
DISPLAY= .venv/bin/python -m voice_assistant
```

Expected: text-mode prompt appears (because GUI auto-detect fails without `$DISPLAY`).

- [ ] **Step 4: Push**

```bash
git push origin main
```

- [ ] **Step 5: Done.**

The next user who runs `curl | bash` from a graphical session gets the desktop app by default.

---

## Done criteria

- `pytest -q` passes (~119 tests).
- `voice-assistant --gui` opens a window matching the design spec.
- Orb animates idle → listening → thinking → speaking based on real orchestrator state.
- Settings drawer reads/writes the same `config.yaml` and `.env` the wizard manages, with stale-key cleanup.
- Hotkey (system-wide) drives a recording → STT → orchestrator → TTS round-trip with the orb's audio-level visualisation tracking the mic.
- `voice-assistant --text` and `voice-assistant --setup` continue to work unchanged.
- `voice-assistant` (no args) auto-selects GUI when a graphical session is available, CLI otherwise.
- `pip install voice-assistant[audio,gmail,desktop] @ git+...` installs PyWebView and the bundled frontend.
- All commits on `main`, pushed to `origin/main`.
