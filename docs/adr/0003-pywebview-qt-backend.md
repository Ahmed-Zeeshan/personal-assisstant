# 0003 — PyWebView (Qt Backend) Instead of Electron / Tauri

**Status:** Accepted  
**Date:** 2026-04-30

## Context

The desktop GUI needs to embed a web view for the conversation interface while
keeping the Python backend. Options evaluated: Electron (ships a full Chromium per
app, ~200 MB overhead, requires Node.js build toolchain), Tauri (Rust toolchain
required, IPC over JSON only), CEF (C++ binding, complex packaging), Tkinter/Qt
native widgets (no HTML/CSS).

## Decision

Use **PyWebView** with the Qt backend (`pywebview>=5`). It delegates to the OS
WebView2 / QtWebEngine and adds ~5 MB to the install. The `bridge.py` JS↔Python
surface is a thin RPC layer with a small, validated callable set.

## Consequences

- No Chromium bundled; rendering quality depends on the OS WebView (acceptable for
  a single-user desktop tool).
- Python-only build pipeline — no Rust/Node.js toolchain required.
- On Linux, QtWebEngine must be present; the installer checks for it.
