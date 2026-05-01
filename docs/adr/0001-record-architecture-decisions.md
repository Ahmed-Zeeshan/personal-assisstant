# 0001 — Record Architecture Decisions

**Status:** Accepted  
**Date:** 2026-04-30

## Context

We need to record significant architectural decisions made during the development of
voice-assistant so that future contributors understand *why* the current design is
the way it is, not just *what* it is.

## Decision

We will use Architecture Decision Records (ADRs) in the MADR format (Michael Nygard /
Markdown Architectural Decision Records). Each ADR is a short file in `docs/adr/`
numbered sequentially. Once accepted, an ADR is immutable except for status changes.

## Consequences

- All significant design choices have a traceable rationale.
- Future contributors can propose superseding ADRs rather than rewriting history.
- The `docs/adr/` directory becomes the canonical source of architectural intent.
