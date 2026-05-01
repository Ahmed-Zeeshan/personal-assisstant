# 0004 — sqlite-vec for Memory Instead of Pinecone / Chroma

**Status:** Accepted  
**Date:** 2026-04-30

## Context

The assistant needs a vector store for semantic memory (`remember` / `recall`).
Options evaluated: Pinecone (cloud-only, API key, latency), Chroma (separate
server process or embedded but heavy Python deps), Qdrant (separate server),
FAISS (no persistence, index management manual).

## Decision

Use **sqlite-vec** — a SQLite extension that adds a `vec0` virtual table for
approximate nearest-neighbour search. The memory database lives at
`~/.voice-assistant/memory.db`, a single file with no daemon.

## Consequences

- Zero extra infrastructure; fully offline; file-based backup.
- ANN quality is sufficient for a personal-scale memory store (hundreds to low
  thousands of facts).
- Not horizontally scalable — acceptable for single-user desktop scope.
- Future encryption-at-rest requires SQLCipher or file-level encryption; tracked
  in the threat model.
