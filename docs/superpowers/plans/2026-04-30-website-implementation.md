# Voice-assistant Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the marketing landing page described in `docs/superpowers/specs/2026-04-30-website-design.md` — a single-page Astro+Tailwind site with an animated-terminal hero and three-OS install tabs backed by canonical install scripts.

**Architecture:** New `website/` directory at the repo root containing a self-contained Astro project. Canonical `install.sh` and `install.ps1` live under `scripts/` and are copied into `website/public/install/` by a `prebuild` Node script so they ship at `/install.sh` and `/install.ps1`. The Python app under `src/` is untouched.

**Tech Stack:** Astro 4.x · Tailwind CSS 3.x · TypeScript · `@fontsource/inter` + `@fontsource/jetbrains-mono` · Lighthouse CI · POSIX bash · PowerShell.

---

## File Structure

**Created:**

```
scripts/
├── install.sh                              # canonical macOS+Linux installer
├── install.ps1                             # canonical Windows installer
└── copy-install-scripts.mjs                # prebuild helper

website/
├── .gitignore                              # ignore node_modules, dist, copied scripts
├── astro.config.mjs                        # Astro config + Tailwind integration
├── tailwind.config.cjs                     # design tokens (colors, type, motion)
├── postcss.config.cjs                      # PostCSS for Tailwind
├── package.json                            # deps + scripts (prebuild, build, check, dev)
├── tsconfig.json                           # TS config (Astro defaults)
├── README.md                               # short dev/deploy notes
├── lighthouserc.cjs                        # Lighthouse CI thresholds
├── public/
│   ├── favicon.svg                         # simple wordmark icon
│   └── og-image.png                        # 1200×630, dark + wordmark
└── src/
    ├── pages/index.astro                   # composes all sections
    ├── layouts/Base.astro                  # html shell, fonts, meta, global styles
    ├── styles/global.css                   # Tailwind base + custom CSS for terminal anim
    ├── data/site.ts                        # copy strings (headline, features, faq…)
    ├── components/
    │   ├── Nav.astro                       # sticky nav + hamburger
    │   ├── Hero.astro                      # headline, eyebrow, CTAs, hosts <TerminalDemo />
    │   ├── TerminalDemo.astro              # animated terminal markup + CSS
    │   ├── TrustStrip.astro                # LLM-provider row
    │   ├── Features.astro                  # 3×2 card grid
    │   ├── HowItWorks.astro                # 4-step flow
    │   ├── InstallTabs.astro               # macOS/Windows/Linux tabs
    │   ├── Safety.astro                    # 4-bullet panel
    │   ├── Faq.astro                       # accordion
    │   └── Footer.astro                    # repo link, license, attribution
    └── scripts/
        ├── terminal-demo.ts                # ~40-line typewriter loop
        ├── install-tabs.ts                 # OS detect + tab switch + copy button
        ├── nav-mobile.ts                   # hamburger toggle
        └── reveal.ts                       # IntersectionObserver fade-up
```

**Modified:**

- `.gitignore` (root) — append `website/node_modules/`, `website/dist/`, `website/public/install/install.sh`, `website/public/install/install.ps1`.

---

## Task 1: Scaffold the Astro project under `website/`

**Files:**
- Create: `website/package.json`
- Create: `website/astro.config.mjs`
- Create: `website/tsconfig.json`
- Create: `website/postcss.config.cjs`
- Create: `website/tailwind.config.cjs`
- Create: `website/.gitignore`
- Create: `website/src/pages/index.astro`
- Modify: `.gitignore` (root)

- [ ] **Step 1: Create `website/package.json`**

```json
{
  "name": "voice-assistant-website",
  "version": "0.0.1",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "astro dev",
    "prebuild": "node ../scripts/copy-install-scripts.mjs",
    "build": "astro build",
    "preview": "astro preview",
    "astro": "astro",
    "check": "astro check && lhci autorun"
  },
  "dependencies": {
    "@astrojs/tailwind": "^5.1.0",
    "@fontsource/inter": "^5.0.18",
    "@fontsource/jetbrains-mono": "^5.0.20",
    "astro": "^4.15.0",
    "tailwindcss": "^3.4.10"
  },
  "devDependencies": {
    "@astrojs/check": "^0.9.3",
    "@lhci/cli": "^0.14.0",
    "typescript": "^5.5.4"
  }
}
```

- [ ] **Step 2: Create `website/astro.config.mjs`**

```js
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  integrations: [tailwind({ applyBaseStyles: false })],
  output: 'static',
  build: { inlineStylesheets: 'auto' },
});
```

- [ ] **Step 3: Create `website/tsconfig.json`**

```json
{ "extends": "astro/tsconfigs/strict" }
```

- [ ] **Step 4: Create `website/postcss.config.cjs`**

```js
module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };
```

- [ ] **Step 5: Create a placeholder `website/tailwind.config.cjs`**

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{astro,html,ts,tsx}'],
  theme: { extend: {} },
  plugins: [],
};
```

(Real tokens are added in Task 2.)

- [ ] **Step 6: Create `website/.gitignore`**

```
node_modules/
dist/
.astro/
.DS_Store
public/install/install.sh
public/install/install.ps1
```

- [ ] **Step 7: Create a placeholder `website/src/pages/index.astro`**

```astro
---
---
<html lang="en">
  <head><meta charset="utf-8" /><title>voice-assistant</title></head>
  <body><h1>placeholder</h1></body>
</html>
```

- [ ] **Step 8: Append to root `.gitignore`**

```
website/node_modules/
website/dist/
website/.astro/
```

- [ ] **Step 9: Install dependencies and verify dev server starts**

```bash
cd website && npm install && npm run dev -- --host 127.0.0.1
```

Expected: Astro dev server reports `Local http://127.0.0.1:4321/` and the placeholder loads. Stop with Ctrl-C.

- [ ] **Step 10: Commit**

```bash
git add website/ .gitignore
git commit -m "feat(website): scaffold Astro + Tailwind project"
```

---

## Task 2: Tailwind theme tokens & Base layout

**Files:**
- Modify: `website/tailwind.config.cjs`
- Create: `website/src/styles/global.css`
- Create: `website/src/layouts/Base.astro`

- [ ] **Step 1: Replace `website/tailwind.config.cjs`** with the full theme

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{astro,html,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0b0d10',
        surface: '#13161b',
        border: '#1f242c',
        fg: '#e6e8eb',
        muted: '#9aa3ad',
        dim: '#6b7280',
        accent: '#7c5cff',
        success: '#34d399',
        warn: '#f59e0b',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        'h1-fluid': ['clamp(2.5rem, 6vw, 4.5rem)', { lineHeight: '1.05', letterSpacing: '-0.02em' }],
        'h2-fluid': ['clamp(1.75rem, 3.5vw, 2.5rem)', { lineHeight: '1.15', letterSpacing: '-0.02em' }],
      },
      transitionTimingFunction: { 'enter': 'cubic-bezier(0.2, 0.8, 0.2, 1)' },
      maxWidth: { 'content': '1200px', 'prose-narrow': '720px' },
    },
  },
  plugins: [],
};
```

- [ ] **Step 2: Create `website/src/styles/global.css`**

```css
@import '@fontsource/inter/400.css';
@import '@fontsource/inter/500.css';
@import '@fontsource/inter/600.css';
@import '@fontsource/inter/700.css';
@import '@fontsource/inter/800.css';
@import '@fontsource/jetbrains-mono/400.css';
@import '@fontsource/jetbrains-mono/500.css';

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html { @apply bg-bg text-fg; -webkit-font-smoothing: antialiased; }
  body { @apply font-sans; }
  ::selection { background: theme('colors.accent'); color: theme('colors.bg'); }
  :focus-visible { outline: 2px solid theme('colors.accent'); outline-offset: 2px; border-radius: 4px; }
}

@layer utilities {
  .container-page { @apply mx-auto w-full max-w-content px-6 md:px-8; }
  .reveal { opacity: 0; transform: translateY(8px); transition: opacity 400ms theme('transitionTimingFunction.enter'), transform 400ms theme('transitionTimingFunction.enter'); }
  .reveal.is-visible { opacity: 1; transform: none; }
  @media (prefers-reduced-motion: reduce) {
    .reveal { opacity: 1; transform: none; transition: none; }
  }
}
```

- [ ] **Step 3: Create `website/src/layouts/Base.astro`**

```astro
---
import '../styles/global.css';
interface Props { title: string; description: string; }
const { title, description } = Astro.props;
---
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="color-scheme" content="dark" />
    <meta name="description" content={description} />
    <meta property="og:title" content={title} />
    <meta property="og:description" content={description} />
    <meta property="og:image" content="/og-image.png" />
    <meta property="og:type" content="website" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
    <title>{title}</title>
  </head>
  <body class="bg-bg text-fg">
    <slot />
  </body>
</html>
```

- [ ] **Step 4: Replace `website/src/pages/index.astro`** with a Base-using placeholder

```astro
---
import Base from '../layouts/Base.astro';
---
<Base title="voice-assistant — talk to your computer" description="A local-first voice assistant for your desktop.">
  <main class="container-page py-24">
    <h1 class="text-h1-fluid font-extrabold">voice-assistant</h1>
    <p class="text-muted mt-4">scaffold checkpoint</p>
  </main>
</Base>
```

- [ ] **Step 5: Run dev server and verify type/colour pipeline**

```bash
cd website && npm run dev -- --host 127.0.0.1
```

Expected: page loads with violet selection colour, dark background, Inter typeface, no console errors.

- [ ] **Step 6: Commit**

```bash
git add website/tailwind.config.cjs website/src/styles/global.css website/src/layouts/Base.astro website/src/pages/index.astro
git commit -m "feat(website): theme tokens, fonts, base layout"
```

---

## Task 3: Site copy data module

**Files:**
- Create: `website/src/data/site.ts`

Centralising copy here keeps components clean and makes future copy edits trivial.

- [ ] **Step 1: Create `website/src/data/site.ts`**

```ts
export const site = {
  brand: 'voice-assistant',
  repoUrl: 'https://github.com/REPLACE-ME/voice-assistant',
  tagline: 'Talk to your computer.',
  subhead: 'A local-first voice assistant that opens apps, manages files, and sends email — driven by the LLM of your choice.',
  eyebrow: 'PHASE 1 · OPEN SOURCE · LOCAL-FIRST',
  navLinks: [
    { href: '#features', label: 'Features' },
    { href: '#install', label: 'Install' },
    { href: '#safety', label: 'Safety' },
  ],
  trust: {
    label: 'Powered by your choice of',
    providers: ['Claude', 'GPT', 'Gemini', 'Ollama'],
  },
  features: [
    { title: 'Voice in', body: 'Global hotkey + faster-whisper. 100% local — audio never leaves your machine.' },
    { title: 'LLM brain', body: 'Pluggable via LiteLLM: Anthropic Claude, OpenAI GPT, Google Gemini, or local Ollama.' },
    { title: 'Voice out', body: 'Piper TTS, fully local. No streaming, no cloud, no per-request cost.' },
    { title: 'File tools', body: 'Create, read, move, delete — scoped to directories you whitelist. Symlink escapes blocked.' },
    { title: 'System tools', body: 'Open URLs and launch desktop apps by name. Safe-by-default URL parsing.' },
    { title: 'Email', body: 'Send mail through Gmail with the gmail.send scope only. No read access ever requested.' },
  ],
  steps: [
    { title: 'Hotkey',     body: 'Press ctrl+shift+space.' },
    { title: 'Transcribe', body: 'faster-whisper, on-device.' },
    { title: 'Decide',     body: 'Your LLM picks a tool.' },
    { title: 'Act + Reply', body: 'Run the tool, speak the result.' },
  ],
  install: {
    macos:   { prereq: 'Requires Python 3.10+ and a microphone.', cmd: 'curl -fsSL https://YOUR-DOMAIN/install.sh | bash', run: 'voice-assistant', note: 'Default hotkey: ctrl+shift+space.' },
    linux:   { prereq: 'Requires Python 3.10+, portaudio, and espeak-ng.', cmd: 'curl -fsSL https://YOUR-DOMAIN/install.sh | bash', run: 'voice-assistant', note: 'Default hotkey: ctrl+shift+space.' },
    windows: { prereq: 'Requires Python 3.10+ and a microphone.', cmd: 'iwr -useb https://YOUR-DOMAIN/install.ps1 | iex', run: 'voice-assistant', note: 'Default hotkey: ctrl+shift+space.' },
  },
  safety: [
    { title: 'Path-scoped filesystem', body: 'Tools refuse paths outside your allowed_roots. Symlink and .. traversal blocked.' },
    { title: 'Destructive-op confirmation', body: 'Deletes and overwrites require explicit confirmation from the brain.' },
    { title: 'Delete rate limit', body: 'A configurable cap on deletes per minute prevents runaway loops.' },
    { title: 'Prompt-injection defence', body: 'The brain treats tool-returned data as untrusted — instructions inside file contents are ignored.' },
  ],
  faq: [
    { q: 'Is my voice sent to the cloud?', a: 'No. Speech-to-text runs locally via faster-whisper. Only the transcribed text is sent to the LLM you configure.' },
    { q: 'Which LLM should I use?',         a: 'Any of Claude, GPT, Gemini, or local Ollama. Pick by cost, capability, or privacy preference — they all support tool use.' },
    { q: 'Does it work offline?',           a: 'Audio in/out is fully local. The LLM brain needs network unless you run Ollama locally.' },
    { q: 'How do I revoke Gmail access?',   a: 'Visit your Google Account → Security → Third-party access and remove "voice-assistant", then delete the cached oauth-token.json.' },
    { q: 'How do I uninstall?',             a: 'Re-run the install command with --uninstall. It removes the venv and launcher symlink and asks before touching your config.' },
    { q: 'Why no mobile or web version?',   a: 'The product runs against your desktop apps and filesystem — that does not exist on mobile or the web.' },
  ],
  footer: {
    author: 'Zeeshan Ahmed',
    license: 'Private — not for redistribution.',
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add website/src/data/site.ts
git commit -m "feat(website): centralised site copy"
```

---

## Task 4: Nav component (sticky + hamburger)

**Files:**
- Create: `website/src/components/Nav.astro`
- Create: `website/src/scripts/nav-mobile.ts`
- Modify: `website/src/pages/index.astro`

- [ ] **Step 1: Create `website/src/components/Nav.astro`**

```astro
---
import { site } from '../data/site';
---
<header id="site-nav" class="fixed top-0 inset-x-0 z-50 transition-colors duration-200 bg-bg/0">
  <div class="container-page flex items-center justify-between h-16">
    <a href="#top" class="font-mono text-sm tracking-tight">{site.brand}</a>

    <nav class="hidden md:flex items-center gap-8 text-sm text-muted">
      {site.navLinks.map((l) => (
        <a href={l.href} class="hover:text-fg transition-colors">{l.label}</a>
      ))}
      <a href={site.repoUrl} class="hover:text-fg transition-colors" aria-label="GitHub">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M12 .3a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2.1c-3.3.7-4-1.6-4-1.6-.6-1.4-1.4-1.8-1.4-1.8-1.1-.7.1-.7.1-.7 1.2.1 1.9 1.3 1.9 1.3 1.1 1.9 2.9 1.4 3.6 1 .1-.8.4-1.4.8-1.7-2.7-.3-5.5-1.3-5.5-6 0-1.3.5-2.4 1.3-3.2-.1-.3-.6-1.6.1-3.3 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.7 1.7.2 3 .1 3.3.8.8 1.3 1.9 1.3 3.2 0 4.7-2.8 5.7-5.5 6 .4.4.8 1.1.8 2.2v3.2c0 .3.2.7.8.6A12 12 0 0 0 12 .3"/>
        </svg>
      </a>
    </nav>

    <button id="nav-toggle" class="md:hidden h-11 w-11 grid place-items-center text-fg" aria-expanded="false" aria-controls="nav-panel" aria-label="Open menu">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
      </svg>
    </button>
  </div>

  <div id="nav-panel" class="md:hidden fixed inset-0 top-16 bg-bg/95 backdrop-blur-sm hidden">
    <nav class="container-page py-8 flex flex-col gap-6 text-lg">
      {site.navLinks.map((l) => (
        <a href={l.href} class="py-3 border-b border-border" data-nav-close>{l.label}</a>
      ))}
      <a href={site.repoUrl} class="py-3 border-b border-border" data-nav-close>GitHub</a>
    </nav>
  </div>
</header>

<script>
  import '../scripts/nav-mobile';
</script>
```

- [ ] **Step 2: Create `website/src/scripts/nav-mobile.ts`**

```ts
const toggle = document.getElementById('nav-toggle');
const panel = document.getElementById('nav-panel');
const nav = document.getElementById('site-nav');

if (toggle && panel) {
  const setOpen = (open: boolean) => {
    panel.classList.toggle('hidden', !open);
    toggle.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
  };
  toggle.addEventListener('click', () => setOpen(panel.classList.contains('hidden')));
  panel.querySelectorAll('[data-nav-close]').forEach((el) =>
    el.addEventListener('click', () => setOpen(false))
  );
}

if (nav) {
  const onScroll = () => {
    const scrolled = window.scrollY > 8;
    nav.classList.toggle('bg-bg/80', scrolled);
    nav.classList.toggle('backdrop-blur-md', scrolled);
    nav.classList.toggle('border-b', scrolled);
    nav.classList.toggle('border-border', scrolled);
  };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
}
```

- [ ] **Step 3: Wire `<Nav />` into `index.astro`**

Replace the body of `index.astro`:

```astro
---
import Base from '../layouts/Base.astro';
import Nav from '../components/Nav.astro';
import { site } from '../data/site';
---
<Base title={`${site.brand} — talk to your computer`} description={site.subhead}>
  <a id="top"></a>
  <Nav />
  <main class="pt-16"><!-- sections will be added next tasks --></main>
</Base>
```

- [ ] **Step 4: Verify in dev server**

```bash
cd website && npm run dev -- --host 127.0.0.1
```

Manual checks: nav stays at the top, becomes solid on scroll, hamburger appears below 768px, panel slides in and locks scroll, GitHub icon links out.

- [ ] **Step 5: Commit**

```bash
git add website/src/components/Nav.astro website/src/scripts/nav-mobile.ts website/src/pages/index.astro
git commit -m "feat(website): nav with sticky scroll + mobile panel"
```

---

## Task 5: Hero component (without terminal yet)

**Files:**
- Create: `website/src/components/Hero.astro`
- Modify: `website/src/pages/index.astro`

- [ ] **Step 1: Create `website/src/components/Hero.astro`**

```astro
---
import { site } from '../data/site';
---
<section class="relative overflow-hidden">
  <div aria-hidden="true" class="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 h-[600px] w-[900px] rounded-full"
       style="background: radial-gradient(closest-side, rgba(124,92,255,0.18), transparent 70%); filter: blur(120px);"></div>

  <div class="container-page relative grid lg:grid-cols-12 gap-12 py-24 md:py-32 items-center">
    <div class="lg:col-span-6 reveal">
      <p class="text-xs font-medium tracking-[0.18em] text-muted">{site.eyebrow}</p>
      <h1 class="mt-4 text-h1-fluid font-extrabold text-fg">
        {site.tagline}
      </h1>
      <p class="mt-6 text-lg md:text-xl text-muted max-w-xl">{site.subhead}</p>
      <div class="mt-8 flex flex-wrap gap-3">
        <a href="#install" class="inline-flex items-center justify-center h-11 px-5 rounded-md bg-accent text-bg font-semibold hover:opacity-90 transition-opacity">Install</a>
        <a href={site.repoUrl} class="inline-flex items-center justify-center h-11 px-5 rounded-md border border-border text-fg hover:bg-surface transition-colors">View on GitHub</a>
      </div>
    </div>

    <div class="lg:col-span-6 reveal">
      <div id="terminal-slot" class="rounded-xl border border-border bg-surface shadow-2xl shadow-black/40 overflow-hidden">
        <div class="px-4 py-2 border-b border-border flex items-center gap-2 text-xs text-dim">
          <span class="h-3 w-3 rounded-full bg-[#ff5f56]"></span>
          <span class="h-3 w-3 rounded-full bg-[#ffbd2e]"></span>
          <span class="h-3 w-3 rounded-full bg-[#27c93f]"></span>
          <span class="ml-2 font-mono">voice-assistant — ~</span>
        </div>
        <div class="p-5 font-mono text-sm md:text-base min-h-[260px]">
          <p class="text-muted">terminal goes here</p>
        </div>
      </div>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Add `<Hero />` to `index.astro`**

Inside the `<main>` element add:

```astro
<Hero />
```

(import at top: `import Hero from '../components/Hero.astro';`)

- [ ] **Step 3: Verify in dev server**

Headline + CTAs render at `lg` two-column, single-column below `lg`. Gradient blob is visible behind the headline. Both CTAs are tab-reachable.

- [ ] **Step 4: Commit**

```bash
git add website/src/components/Hero.astro website/src/pages/index.astro
git commit -m "feat(website): hero with headline, CTAs, terminal placeholder"
```

---

## Task 6: TerminalDemo animation

**Files:**
- Create: `website/src/components/TerminalDemo.astro`
- Create: `website/src/scripts/terminal-demo.ts`
- Modify: `website/src/components/Hero.astro`

- [ ] **Step 1: Create `website/src/components/TerminalDemo.astro`**

```astro
---
---
<div class="rounded-xl border border-border bg-surface shadow-2xl shadow-black/40 overflow-hidden"
     aria-label="Demo of voice-assistant creating a folder by voice command">
  <div class="px-4 py-2 border-b border-border flex items-center gap-2 text-xs text-dim">
    <span class="h-3 w-3 rounded-full bg-[#ff5f56]"></span>
    <span class="h-3 w-3 rounded-full bg-[#ffbd2e]"></span>
    <span class="h-3 w-3 rounded-full bg-[#27c93f]"></span>
    <span class="ml-2 font-mono">voice-assistant — ~</span>
  </div>

  <div id="terminal-body" class="p-5 font-mono text-sm md:text-base min-h-[260px] leading-7" data-loop>
    <div class="t-line" data-line="0"><span class="text-dim">$&nbsp;</span><span data-typed></span><span class="t-cursor">▍</span></div>
    <div class="t-line opacity-0" data-line="1"><span class="text-success">●</span> Listening… press <span class="text-fg">ctrl+shift+space</span></div>
    <div class="t-line opacity-0" data-line="2"><span class="text-fg">🎙</span> "Create a folder called notes on my desktop"
      <span class="t-meter inline-flex gap-[2px] align-middle ml-2"></span>
    </div>
    <div class="t-line opacity-0 text-dim" data-line="3">↳ transcribed</div>
    <div class="t-line opacity-0" data-line="4"><span class="text-muted">brain → tool:</span> <span data-typed-2></span></div>
    <div class="t-line opacity-0" data-line="5"><span class="text-success">✓</span> folder created</div>
    <div class="t-line opacity-0" data-line="6"><span class="text-accent">🔊</span> "Done. Created notes on your desktop."</div>
    <div class="t-line opacity-0" data-line="7"><span class="text-success">●</span> Listening…</div>
  </div>
</div>

<style>
  .t-line { transform: translateY(6px); transition: opacity 400ms cubic-bezier(0.2,0.8,0.2,1), transform 400ms cubic-bezier(0.2,0.8,0.2,1); }
  .t-line.is-on { opacity: 1; transform: none; }
  .t-cursor { display: inline-block; width: 0.6ch; animation: blink 1.05s steps(2, end) infinite; }
  .t-meter span { display: inline-block; width: 2px; height: 12px; background: theme('colors.accent'); opacity: 0.7; }
  @keyframes blink { 50% { opacity: 0; } }
  @keyframes vu { 0%,100% { transform: scaleY(0.4); } 50% { transform: scaleY(1); } }
  .t-meter.is-on span { animation: vu 0.6s ease-in-out infinite; }
  .t-meter.is-on span:nth-child(2n)  { animation-delay: 0.05s; }
  .t-meter.is-on span:nth-child(3n)  { animation-delay: 0.10s; }
  .t-meter.is-on span:nth-child(5n)  { animation-delay: 0.15s; }

  @media (prefers-reduced-motion: reduce) {
    .t-line { opacity: 1 !important; transform: none !important; transition: none; }
    .t-cursor, .t-meter.is-on span { animation: none; opacity: 0; }
    [data-typed]::after, [data-typed-2]::after { content: 'voice-assistant'; }
    [data-typed-2]::after { content: 'create_folder(path="~/Desktop/notes")'; }
  }
</style>

<script>
  import '../scripts/terminal-demo';
</script>
```

- [ ] **Step 2: Create `website/src/scripts/terminal-demo.ts`**

```ts
const root = document.querySelector<HTMLElement>('[data-loop]');
if (root && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const lines = Array.from(root.querySelectorAll<HTMLElement>('.t-line'));
  const typed1 = root.querySelector<HTMLElement>('[data-typed]');
  const typed2 = root.querySelector<HTMLElement>('[data-typed-2]');
  const meter = root.querySelector<HTMLElement>('.t-meter');
  if (meter) {
    for (let i = 0; i < 20; i++) meter.appendChild(document.createElement('span'));
  }

  const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

  async function type(el: HTMLElement | null, text: string, perChar = 35) {
    if (!el) return;
    el.textContent = '';
    for (const ch of text) { el.textContent += ch; await sleep(perChar); }
  }

  function show(idx: number) { lines[idx]?.classList.add('is-on'); }
  function hideAll() { lines.forEach((l) => l.classList.remove('is-on')); if (typed1) typed1.textContent = ''; if (typed2) typed2.textContent = ''; meter?.classList.remove('is-on'); }

  async function loop() {
    while (true) {
      hideAll();
      show(0);
      await type(typed1, 'voice-assistant');
      await sleep(700);
      show(1); await sleep(1500);
      show(2); meter?.classList.add('is-on'); await sleep(1000); meter?.classList.remove('is-on');
      show(3); await sleep(1000);
      show(4); await type(typed2, 'create_folder(path="~/Desktop/notes")', 22);
      await sleep(700);
      show(5); await sleep(1000);
      show(6); await sleep(2000);
      show(7); await sleep(2500);
    }
  }

  // Pause when not visible to save battery
  const io = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) { io.disconnect(); loop(); }
  }, { rootMargin: '0px 0px -10% 0px' });
  io.observe(root);
}
```

- [ ] **Step 3: Replace the placeholder block in `Hero.astro`** with `<TerminalDemo />`

Replace the inner `<div id="terminal-slot">…</div>` with:

```astro
<TerminalDemo />
```

(import at top of `Hero.astro`: `import TerminalDemo from './TerminalDemo.astro';`)

- [ ] **Step 4: Verify in dev server**

The terminal types `voice-assistant`, listens, shows the voice line with VU meter pulses, then the tool-call line types in. Loop restarts. With OS-level reduced motion enabled, animation is replaced by the static end frame.

- [ ] **Step 5: Commit**

```bash
git add website/src/components/TerminalDemo.astro website/src/scripts/terminal-demo.ts website/src/components/Hero.astro
git commit -m "feat(website): animated terminal demo with reduced-motion fallback"
```

---

## Task 7: TrustStrip + Features components

**Files:**
- Create: `website/src/components/TrustStrip.astro`
- Create: `website/src/components/Features.astro`
- Modify: `website/src/pages/index.astro`

- [ ] **Step 1: Create `website/src/components/TrustStrip.astro`**

```astro
---
import { site } from '../data/site';
---
<section class="border-y border-border bg-surface/40">
  <div class="container-page py-8 flex flex-wrap items-center justify-center gap-x-10 gap-y-3 text-sm">
    <span class="text-muted">{site.trust.label}</span>
    {site.trust.providers.map((p) => (
      <span class="font-semibold text-fg">{p}</span>
    ))}
  </div>
</section>
```

- [ ] **Step 2: Create `website/src/components/Features.astro`**

```astro
---
import { site } from '../data/site';
---
<section id="features" class="container-page py-24 md:py-32">
  <h2 class="text-h2-fluid font-bold reveal">Everything you need. Nothing you don't.</h2>
  <p class="mt-4 text-muted max-w-prose-narrow reveal">Six built-in tools, each with a tight surface area and explicit safety rules.</p>

  <ul class="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    {site.features.map((f) => (
      <li class="reveal rounded-xl border border-border bg-surface p-6 hover:border-accent/40 transition-colors">
        <h3 class="font-semibold text-fg">{f.title}</h3>
        <p class="mt-2 text-sm text-muted leading-6">{f.body}</p>
      </li>
    ))}
  </ul>
</section>
```

- [ ] **Step 3: Add both into `index.astro`** in order: `<Hero /> → <TrustStrip /> → <Features />`

- [ ] **Step 4: Verify in dev server**

Trust strip is single row on desktop, wraps on small screens. Features grid: 1 col below 640px, 2 cols 640–1024px, 3 cols above.

- [ ] **Step 5: Commit**

```bash
git add website/src/components/TrustStrip.astro website/src/components/Features.astro website/src/pages/index.astro
git commit -m "feat(website): trust strip + features grid"
```

---

## Task 8: HowItWorks component

**Files:**
- Create: `website/src/components/HowItWorks.astro`
- Modify: `website/src/pages/index.astro`

- [ ] **Step 1: Create `website/src/components/HowItWorks.astro`**

```astro
---
import { site } from '../data/site';
---
<section class="border-t border-border">
  <div class="container-page py-24 md:py-32">
    <h2 class="text-h2-fluid font-bold reveal">How it works</h2>
    <ol class="mt-12 grid gap-6 md:grid-cols-4">
      {site.steps.map((s, i) => (
        <li class="reveal relative rounded-xl border border-border bg-surface p-6">
          <div class="font-mono text-xs text-accent">{String(i + 1).padStart(2, '0')}</div>
          <h3 class="mt-2 font-semibold">{s.title}</h3>
          <p class="mt-2 text-sm text-muted leading-6">{s.body}</p>
          {i < site.steps.length - 1 && (
            <span aria-hidden="true" class="hidden md:block absolute top-1/2 -right-3 text-dim">→</span>
          )}
          {i < site.steps.length - 1 && (
            <span aria-hidden="true" class="md:hidden block text-center text-dim mt-4">↓</span>
          )}
        </li>
      ))}
    </ol>
  </div>
</section>
```

- [ ] **Step 2: Add `<HowItWorks />` to `index.astro`** after `<Features />`

- [ ] **Step 3: Verify in dev server**

Vertical stack with down-arrows on mobile, horizontal flow with right-arrows on `md+`.

- [ ] **Step 4: Commit**

```bash
git add website/src/components/HowItWorks.astro website/src/pages/index.astro
git commit -m "feat(website): how-it-works flow"
```

---

## Task 9: InstallTabs component

**Files:**
- Create: `website/src/components/InstallTabs.astro`
- Create: `website/src/scripts/install-tabs.ts`
- Modify: `website/src/pages/index.astro`

- [ ] **Step 1: Create `website/src/components/InstallTabs.astro`**

```astro
---
import { site } from '../data/site';
const oses = [
  { id: 'macos',   label: 'macOS',   data: site.install.macos },
  { id: 'windows', label: 'Windows', data: site.install.windows },
  { id: 'linux',   label: 'Linux',   data: site.install.linux },
];
---
<section id="install" class="container-page py-24 md:py-32">
  <h2 class="text-h2-fluid font-bold reveal">Install</h2>
  <p class="mt-4 text-muted max-w-prose-narrow reveal">One command. Drops a venv into your home directory, no admin rights, no global Python pollution.</p>

  <div class="mt-10 reveal" data-install-tabs>
    <div role="tablist" aria-label="Operating system" class="flex flex-wrap gap-2 sm:gap-4 border-b border-border">
      {oses.map((os) => (
        <button role="tab" aria-selected={os.id === 'macos'} data-tab={os.id}
                class="h-11 px-4 sm:px-5 rounded-t-md text-sm font-medium text-muted aria-selected:text-fg aria-selected:border-b-2 aria-selected:border-accent transition-colors">
          {os.label}
        </button>
      ))}
    </div>

    {oses.map((os) => (
      <div role="tabpanel" data-panel={os.id} class:list={['py-6 grid gap-5', os.id === 'macos' ? '' : 'hidden']}>
        <p class="text-sm text-muted">{os.data.prereq}</p>

        <div class="rounded-lg border border-border bg-surface flex items-stretch overflow-hidden">
          <pre class="font-mono text-sm md:text-base px-4 py-3 overflow-x-auto flex-1"><code>{os.data.cmd}</code></pre>
          <button data-copy={os.data.cmd}
                  class="px-4 border-l border-border text-sm text-muted hover:text-fg hover:bg-bg/40 transition-colors"
                  aria-label={`Copy install command for ${os.label}`}>Copy</button>
        </div>

        <div class="text-sm text-muted">
          Then run <code class="font-mono text-fg bg-surface px-1.5 py-0.5 rounded">{os.data.run}</code>. {os.data.note}
        </div>
      </div>
    ))}

    <details class="mt-10 group">
      <summary class="cursor-pointer text-sm text-muted hover:text-fg list-none">Or install from source ▾</summary>
      <div class="mt-4 rounded-lg border border-border bg-surface p-4 font-mono text-sm overflow-x-auto">
<pre><code>git clone {site.repoUrl}
cd voice-assistant
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[audio,gmail,dev]"
cp config.yaml.example config.yaml
cp .env.example .env
voice-assistant</code></pre>
      </div>
    </details>
  </div>
</section>

<script>
  import '../scripts/install-tabs';
</script>
```

- [ ] **Step 2: Create `website/src/scripts/install-tabs.ts`**

```ts
const root = document.querySelector<HTMLElement>('[data-install-tabs]');
if (root) {
  const tabs = Array.from(root.querySelectorAll<HTMLButtonElement>('[data-tab]'));
  const panels = Array.from(root.querySelectorAll<HTMLElement>('[data-panel]'));

  function activate(id: string) {
    tabs.forEach((t) => t.setAttribute('aria-selected', String(t.dataset.tab === id)));
    panels.forEach((p) => p.classList.toggle('hidden', p.dataset.panel !== id));
  }

  // Auto-detect OS on first load
  const ua = (navigator as any).userAgentData?.platform ?? navigator.platform ?? '';
  const lower = ua.toLowerCase();
  let initial = 'macos';
  if (lower.includes('win')) initial = 'windows';
  else if (lower.includes('linux')) initial = 'linux';
  else if (lower.includes('mac')) initial = 'macos';
  activate(initial);

  tabs.forEach((t) => t.addEventListener('click', () => activate(t.dataset.tab!)));

  // Copy buttons
  root.querySelectorAll<HTMLButtonElement>('[data-copy]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(btn.dataset.copy ?? '');
        const original = btn.textContent;
        btn.textContent = '✓ Copied';
        setTimeout(() => { btn.textContent = original; }, 1500);
      } catch {
        btn.textContent = 'Copy failed';
      }
    });
  });
}
```

- [ ] **Step 3: Add `<InstallTabs />` to `index.astro`** after `<HowItWorks />`

- [ ] **Step 4: Verify in dev server**

Open in Chrome, Firefox, Safari (or DevTools UA spoofing). The correct tab auto-selects per OS. Copy button copies the command and shows ✓ for 1.5s. The "Or install from source" disclosure expands.

- [ ] **Step 5: Commit**

```bash
git add website/src/components/InstallTabs.astro website/src/scripts/install-tabs.ts website/src/pages/index.astro
git commit -m "feat(website): install tabs with OS auto-detect and copy"
```

---

## Task 10: Safety, Faq, and Footer components

**Files:**
- Create: `website/src/components/Safety.astro`
- Create: `website/src/components/Faq.astro`
- Create: `website/src/components/Footer.astro`
- Modify: `website/src/pages/index.astro`

- [ ] **Step 1: Create `website/src/components/Safety.astro`**

```astro
---
import { site } from '../data/site';
---
<section id="safety" class="border-t border-border">
  <div class="container-page py-24 md:py-32">
    <h2 class="text-h2-fluid font-bold reveal">Safety, by default.</h2>
    <p class="mt-4 text-muted max-w-prose-narrow reveal">An LLM holding root on your filesystem is a bad time. The runtime puts walls in the right places.</p>

    <ul class="mt-10 grid gap-4 sm:grid-cols-2">
      {site.safety.map((s) => (
        <li class="reveal rounded-xl border border-border bg-surface p-6">
          <h3 class="font-semibold flex items-center gap-2">
            <span aria-hidden="true" class="text-success">●</span>
            {s.title}
          </h3>
          <p class="mt-2 text-sm text-muted leading-6">{s.body}</p>
        </li>
      ))}
    </ul>
  </div>
</section>
```

- [ ] **Step 2: Create `website/src/components/Faq.astro`**

```astro
---
import { site } from '../data/site';
---
<section class="border-t border-border">
  <div class="container-page py-24 md:py-32 max-w-prose-narrow">
    <h2 class="text-h2-fluid font-bold reveal">Frequently asked</h2>
    <dl class="mt-10 divide-y divide-border">
      {site.faq.map((item) => (
        <details class="group py-5 reveal">
          <summary class="cursor-pointer flex items-center justify-between list-none">
            <dt class="font-medium text-fg pr-6">{item.q}</dt>
            <span aria-hidden="true" class="text-dim group-open:rotate-45 transition-transform">+</span>
          </summary>
          <dd class="mt-3 text-sm text-muted leading-6">{item.a}</dd>
        </details>
      ))}
    </dl>
  </div>
</section>
```

- [ ] **Step 3: Create `website/src/components/Footer.astro`**

```astro
---
import { site } from '../data/site';
---
<footer class="border-t border-border">
  <div class="container-page py-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4 text-sm text-muted">
    <div>© {new Date().getFullYear()} {site.footer.author}. {site.footer.license}</div>
    <div class="flex gap-6">
      <a href={site.repoUrl} class="hover:text-fg transition-colors">GitHub</a>
      <a href="#top" class="hover:text-fg transition-colors">Back to top</a>
    </div>
  </div>
</footer>
```

- [ ] **Step 4: Wire all three into `index.astro`** in order: `<Safety /> → <Faq /> → <Footer />`

- [ ] **Step 5: Verify in dev server**

Safety section reads as 4 bullets, Faq accordion opens/closes one at a time per click (browser default for `<details>`), footer is a single row on desktop and stacked on mobile.

- [ ] **Step 6: Commit**

```bash
git add website/src/components/Safety.astro website/src/components/Faq.astro website/src/components/Footer.astro website/src/pages/index.astro
git commit -m "feat(website): safety, faq, footer"
```

---

## Task 11: Scroll-reveal IntersectionObserver

**Files:**
- Create: `website/src/scripts/reveal.ts`
- Modify: `website/src/layouts/Base.astro`

- [ ] **Step 1: Create `website/src/scripts/reveal.ts`**

```ts
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (!reduce) {
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) {
        e.target.classList.add('is-visible');
        io.unobserve(e.target);
      }
    }
  }, { threshold: 0.1, rootMargin: '0px 0px -8% 0px' });

  document.querySelectorAll('.reveal').forEach((el) => io.observe(el));
} else {
  document.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-visible'));
}
```

- [ ] **Step 2: Add the script tag to `Base.astro`** just before `</body>`:

```astro
    <script>
      import '../scripts/reveal';
    </script>
  </body>
</html>
```

- [ ] **Step 3: Verify in dev server**

Sections fade up and translate as they enter the viewport, only once. With reduced motion, sections appear immediately.

- [ ] **Step 4: Commit**

```bash
git add website/src/scripts/reveal.ts website/src/layouts/Base.astro
git commit -m "feat(website): scroll-reveal IntersectionObserver"
```

---

## Task 12: Static assets — favicon and OG image

**Files:**
- Create: `website/public/favicon.svg`
- Create: `website/public/og-image.png` (binary, 1200×630)

- [ ] **Step 1: Create `website/public/favicon.svg`**

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#0b0d10"/>
  <circle cx="16" cy="16" r="4" fill="#7c5cff"/>
  <circle cx="16" cy="16" r="9" fill="none" stroke="#7c5cff" stroke-width="1.5" opacity="0.5"/>
  <circle cx="16" cy="16" r="13" fill="none" stroke="#7c5cff" stroke-width="1" opacity="0.25"/>
</svg>
```

- [ ] **Step 2: Generate `website/public/og-image.png`**

Use any tool that produces a 1200×630 PNG with: `#0b0d10` background, the wordmark `voice-assistant` in Inter 800 white at 80px centred, and the tagline below in Inter 500 muted at 32px. A one-shot way:

```bash
# from repo root, requires ImageMagick + Inter-Regular.ttf available locally
magick -size 1200x630 xc:'#0b0d10' \
  -font Inter-ExtraBold -pointsize 96 -fill '#e6e8eb' -gravity center -annotate +0-40 'voice-assistant' \
  -font Inter-Medium -pointsize 32 -fill '#9aa3ad' -annotate +0+50 'Talk to your computer.' \
  website/public/og-image.png
```

If ImageMagick is unavailable, design the file by hand and save it. The file must exist before Task 14's Lighthouse run.

- [ ] **Step 3: Verify the favicon shows up**

Hard-refresh the dev server tab; the violet-ringed icon should appear.

- [ ] **Step 4: Commit**

```bash
git add website/public/favicon.svg website/public/og-image.png
git commit -m "feat(website): favicon and og image"
```

---

## Task 13: Canonical install scripts + prebuild copier

**Files:**
- Create: `scripts/install.sh`
- Create: `scripts/install.ps1`
- Create: `scripts/copy-install-scripts.mjs`

- [ ] **Step 1: Create `scripts/install.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/REPLACE-ME/voice-assistant"
VA_HOME="${VA_HOME:-$HOME/.local/share/voice-assistant}"
LAUNCHER_DIR="${HOME}/.local/bin"
CONFIG_DIR="${HOME}/.voice-assistant"

say()  { printf '\033[1;35m>>> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!!! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31mxxx %s\033[0m\n' "$*" >&2; exit 1; }

uninstall() {
  say "removing $VA_HOME"
  rm -rf "$VA_HOME"
  rm -f "$LAUNCHER_DIR/voice-assistant"
  if [ -d "$CONFIG_DIR" ]; then
    read -rp "Also delete $CONFIG_DIR (holds OAuth tokens & config)? [y/N] " ans
    case "$ans" in y|Y) rm -rf "$CONFIG_DIR" ;; esac
  fi
  say "uninstalled."
  exit 0
}

[ "${1:-}" = "--uninstall" ] && uninstall

OS="$(uname -s)"
case "$OS" in
  Darwin|Linux) ;;
  *) die "Unsupported OS: $OS. Use install.ps1 on Windows." ;;
esac

command -v python3 >/dev/null || die "python3 not found. Install Python ≥3.10 from https://www.python.org/downloads/."
PY_VER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
case "$PY_VER" in
  3.10|3.11|3.12|3.13|3.14) ;;
  *) die "Python 3.10+ required (found $PY_VER)." ;;
esac

if [ "$OS" = "Linux" ]; then
  if ! pkg-config --exists portaudio-2.0 2>/dev/null && ! ldconfig -p 2>/dev/null | grep -q libportaudio; then
    if   command -v apt-get >/dev/null; then warn "Missing portaudio. Run: sudo apt-get install -y portaudio19-dev espeak-ng"
    elif command -v dnf     >/dev/null; then warn "Missing portaudio. Run: sudo dnf install -y portaudio-devel espeak-ng"
    elif command -v pacman  >/dev/null; then warn "Missing portaudio. Run: sudo pacman -S --needed portaudio espeak-ng"
    else                                     warn "Install portaudio and espeak-ng from your package manager."
    fi
    die "audio prerequisites missing"
  fi
fi

say "installing into $VA_HOME"
mkdir -p "$VA_HOME" "$LAUNCHER_DIR" "$CONFIG_DIR"

say "creating venv"
python3 -m venv "$VA_HOME/.venv"

say "installing voice-assistant from $REPO_URL"
"$VA_HOME/.venv/bin/pip" install --upgrade pip >/dev/null
"$VA_HOME/.venv/bin/pip" install "voice-assistant[audio,gmail] @ git+$REPO_URL"

say "linking launcher → $LAUNCHER_DIR/voice-assistant"
ln -sf "$VA_HOME/.venv/bin/voice-assistant" "$LAUNCHER_DIR/voice-assistant"

case ":$PATH:" in
  *":$LAUNCHER_DIR:"*) ;;
  *) warn "$LAUNCHER_DIR is not on PATH. Add this to your shell rc: export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac

if [ ! -f "$CONFIG_DIR/config.yaml" ] && [ -f "$VA_HOME/.venv/share/voice-assistant/config.yaml.example" ]; then
  cp "$VA_HOME/.venv/share/voice-assistant/config.yaml.example" "$CONFIG_DIR/config.yaml"
  say "seeded $CONFIG_DIR/config.yaml from example"
fi

say "done. Set your API key in $CONFIG_DIR/.env, then run: voice-assistant"
```

- [ ] **Step 2: Create `scripts/install.ps1`**

```powershell
$ErrorActionPreference = 'Stop'

$RepoUrl     = 'https://github.com/REPLACE-ME/voice-assistant'
$VaHome      = if ($env:VA_HOME) { $env:VA_HOME } else { Join-Path $env:LOCALAPPDATA 'voice-assistant' }
$ConfigDir   = Join-Path $env:APPDATA 'voice-assistant'
$LauncherDir = Join-Path $env:LOCALAPPDATA 'Programs\voice-assistant'

function Say  ($m) { Write-Host ">>> $m" -ForegroundColor Magenta }
function Warn ($m) { Write-Host "!!! $m" -ForegroundColor Yellow  }
function Die  ($m) { Write-Host "xxx $m" -ForegroundColor Red; exit 1 }

if ($args[0] -eq '--uninstall') {
  Say "removing $VaHome"
  Remove-Item -Recurse -Force $VaHome -ErrorAction SilentlyContinue
  Remove-Item -Recurse -Force $LauncherDir -ErrorAction SilentlyContinue
  if (Test-Path $ConfigDir) {
    $ans = Read-Host "Also delete $ConfigDir (holds OAuth tokens & config)? [y/N]"
    if ($ans -match '^[yY]$') { Remove-Item -Recurse -Force $ConfigDir }
  }
  Say "uninstalled."
  exit 0
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) { Die "python not found. Install Python ≥3.10 from https://www.python.org/downloads/." }

$pyVer = & python -c "import sys; print('%d.%d' % sys.version_info[:2])"
if (-not ($pyVer -in @('3.10','3.11','3.12','3.13','3.14'))) { Die "Python 3.10+ required (found $pyVer)." }

Say "installing into $VaHome"
New-Item -ItemType Directory -Force -Path $VaHome,$ConfigDir,$LauncherDir | Out-Null

Say "creating venv"
& python -m venv (Join-Path $VaHome '.venv')

$pip = Join-Path $VaHome '.venv\Scripts\pip.exe'
$exe = Join-Path $VaHome '.venv\Scripts\voice-assistant.exe'

Say "installing voice-assistant from $RepoUrl"
& $pip install --upgrade pip | Out-Null
& $pip install "voice-assistant[audio,gmail] @ git+$RepoUrl"

Say "creating launcher shortcut at $LauncherDir\voice-assistant.cmd"
@"
@echo off
"$exe" %*
"@ | Set-Content -Encoding ASCII (Join-Path $LauncherDir 'voice-assistant.cmd')

if (-not ($env:Path -split ';' | Where-Object { $_ -eq $LauncherDir })) {
  Warn "$LauncherDir is not on PATH. Add it via System → Environment Variables, or run:"
  Warn "  [Environment]::SetEnvironmentVariable('Path', `$env:Path + ';$LauncherDir', 'User')"
}

Say "done. Set your API key in $ConfigDir\.env, then run: voice-assistant"
```

- [ ] **Step 3: Create `scripts/copy-install-scripts.mjs`**

```js
import { copyFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, '..');
const dest = join(repoRoot, 'website', 'public', 'install');

mkdirSync(dest, { recursive: true });
copyFileSync(join(here, 'install.sh'),  join(dest, 'install.sh'));
copyFileSync(join(here, 'install.ps1'), join(dest, 'install.ps1'));
console.log(`copied install scripts → ${dest}`);
```

- [ ] **Step 4: Mark `install.sh` executable**

```bash
chmod +x scripts/install.sh
```

- [ ] **Step 5: Run shellcheck (or skip if not installed)**

```bash
shellcheck scripts/install.sh || echo "shellcheck not installed; skipping"
```

Expected: no warnings (or "shellcheck not installed").

- [ ] **Step 6: Verify the prebuild copy works**

```bash
cd website && npm run prebuild
ls public/install/
```

Expected: both `install.sh` and `install.ps1` are present.

- [ ] **Step 7: Verify they serve from the dev server**

```bash
cd website && npm run dev -- --host 127.0.0.1 &
sleep 3
curl -fsSL http://127.0.0.1:4321/install.sh | head -5
curl -fsSL http://127.0.0.1:4321/install.ps1 | head -5
kill %1
```

Expected: the first 5 lines of each file print.

- [ ] **Step 8: Commit**

```bash
git add scripts/ website/.gitignore
git commit -m "feat(install): canonical install.sh + install.ps1 + website prebuild copy"
```

---

## Task 14: Lighthouse CI thresholds + production build

**Files:**
- Create: `website/lighthouserc.cjs`
- Modify: `website/package.json` (already wired to `lhci autorun` in Task 1 — verify)

- [ ] **Step 1: Create `website/lighthouserc.cjs`**

```js
module.exports = {
  ci: {
    collect: {
      staticDistDir: './dist',
      url: ['http://localhost/index.html'],
      numberOfRuns: 1,
    },
    assert: {
      assertions: {
        'categories:performance':     ['error', { minScore: 0.90 }],
        'categories:accessibility':   ['error', { minScore: 0.95 }],
        'categories:best-practices':  ['error', { minScore: 0.95 }],
        'categories:seo':             ['error', { minScore: 0.95 }],
      },
    },
    upload: { target: 'temporary-public-storage' },
  },
};
```

- [ ] **Step 2: Run a production build**

```bash
cd website && npm run build
```

Expected: `dist/` contains `index.html`, `install/install.sh`, `install/install.ps1`, hashed CSS, hashed JS, and the favicon. No build errors.

- [ ] **Step 3: Run `npm run check`**

```bash
cd website && npm run check
```

Expected: `astro check` reports 0 errors, 0 warnings; Lighthouse reports performance ≥0.90, accessibility ≥0.95, best-practices ≥0.95, SEO ≥0.95.

If a metric fails, address the specific failure (e.g. an image without `width`/`height` attributes, missing `lang` on `<html>`, contrast issue) and re-run. Do not lower the thresholds.

- [ ] **Step 4: Sanity-check final CSS size**

```bash
ls -lh website/dist/_astro/*.css | awk '{print $5, $9}'
```

Expected: total CSS < 30 KB.

- [ ] **Step 5: Commit**

```bash
git add website/lighthouserc.cjs
git commit -m "ci(website): Lighthouse thresholds (perf 90 / a11y 95 / bp 95 / seo 95)"
```

---

## Task 15: Manual responsive verification

**Files:**
- Create: `website/README.md`

- [ ] **Step 1: Run `npm run preview` and verify each breakpoint**

```bash
cd website && npm run preview -- --host 127.0.0.1
```

Open the site in Chrome DevTools' device toolbar at: 360, 414, 768, 1024, 1440, 1920. Verify the section-by-section adaptations from the spec (`docs/superpowers/specs/2026-04-30-website-design.md` § "Responsive strategy"):

- 360px: Nav is a hamburger; Hero stacks; Features 1-col; HowItWorks vertical with ↓ arrows; Install tabs as pills; FAQ full-width; footer stacked.
- 768px: Nav full row; Features 2-col; HowItWorks horizontal with → arrows; Install tabs as regular tabs.
- 1024px: Hero is two-column with terminal at ~55% width; Features 3-col.
- 1440 / 1920: Content is centred at max 1200px; nothing stretches edge-to-edge.

Fix any issues directly in the relevant component.

- [ ] **Step 2: Verify keyboard navigation and focus rings**

Tab through every interactive element on desktop. Every focusable element must show the violet focus ring.

- [ ] **Step 3: Verify reduced motion**

In DevTools → Rendering → "Emulate CSS media feature `prefers-reduced-motion: reduce`". Reload. Sections appear without fade-up, terminal animation freezes on the final frame.

- [ ] **Step 4: Create `website/README.md`** (short dev/deploy notes)

```markdown
# voice-assistant website

Single-page marketing site. Astro + Tailwind, static output.

## Develop

```
npm install
npm run dev
```

## Build

```
npm run build       # produces ./dist
npm run preview     # serves ./dist locally
npm run check       # astro check + lighthouse CI
```

## Deploy

Point Vercel, Cloudflare Pages, or GitHub Pages at this directory.
Build command: `npm run build`. Output directory: `dist`.

The canonical install scripts live at `../scripts/install.{sh,ps1}` and are
copied into `public/install/` by the `prebuild` script.

See `../docs/superpowers/specs/2026-04-30-website-design.md` for the design.
```

- [ ] **Step 5: Commit**

```bash
git add website/README.md
git commit -m "docs(website): dev/deploy README"
```

---

## Task 16: Final sweep — replace placeholders & ship

**Files:**
- Modify: `website/src/data/site.ts`
- Modify: `scripts/install.sh`
- Modify: `scripts/install.ps1`

The plan deliberately uses two placeholder strings that must be set before the site is useful:

- `REPLACE-ME` in the GitHub URL — appears in `site.ts` (`repoUrl`) and both install scripts (`REPO_URL` / `$RepoUrl`).
- `YOUR-DOMAIN` in the install commands shown on the page — appears three times in `site.ts` (`install.macos.cmd`, `install.linux.cmd`, `install.windows.cmd`).

- [ ] **Step 1: Replace `REPLACE-ME` with the real GitHub user/org**

```bash
grep -rln 'REPLACE-ME' scripts/ website/src/
# Manually edit each file with the real org/user.
```

- [ ] **Step 2: Replace `YOUR-DOMAIN` with the deployment domain**

If the domain is not finalised, leave a sentinel like `voice-assistant.example.com` so it's visibly wrong rather than confusing.

```bash
grep -rln 'YOUR-DOMAIN' website/src/
```

- [ ] **Step 3: Smoke-test the canonical install on a real machine**

On macOS or Linux:

```bash
bash scripts/install.sh
voice-assistant --text   # set an API key first
bash scripts/install.sh --uninstall
```

This proves the script does not corrupt PATH, leaves the user's config alone unless asked, and uninstalls cleanly.

- [ ] **Step 4: Final production build + Lighthouse**

```bash
cd website && npm run build && npm run check
```

Expected: all thresholds pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/ website/src/data/site.ts
git commit -m "chore(website): set canonical repo URL and domain"
```

---

## Done criteria

- `npm run build && npm run check` passes from a clean checkout.
- The four Lighthouse categories all meet their thresholds.
- `curl -fsSL https://<domain>/install.sh | bash` produces a working `voice-assistant` binary on macOS and Linux; the PowerShell equivalent works on Windows.
- The site is fully usable at 360px and at 1920px with no horizontal scroll, broken layout, or unreadable text.
- All 16 tasks committed; no `REPLACE-ME` or `YOUR-DOMAIN` strings remain.
