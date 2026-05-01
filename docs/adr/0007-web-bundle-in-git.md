# 0007 — Ship the Web Bundle in Git (Not Built at Install Time)

**Status:** Accepted  
**Date:** 2026-04-30

## Context

The desktop GUI web assets (`src/voice_assistant/desktop/web_dist/`) are the
compiled output of `web/` (Vite + TypeScript + Tailwind). Two distribution
strategies were considered:

1. **Build at install time** — require Node.js at install; add a build step to
   the Python install hook.
2. **Commit compiled assets** — check the `web_dist/` directory into git;
   Python packaging includes it via `MANIFEST.in` / `package-data`.

## Decision

Commit the compiled `web_dist/` bundle in git. The CI `web-bundle` job rebuilds
the bundle and fails if the output differs from what is committed, acting as a
consistency check.

## Consequences

- End users install from PyPI without needing Node.js or npm.
- PRs that change `web/` must also update `web_dist/` — enforced by CI.
- Binary/minified assets in git inflate repository size slightly; acceptable for
  a personal-tool project.
