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
