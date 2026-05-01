# 0002 — Piper for Offline TTS, OpenAI TTS for Multilingual

**Status:** Accepted  
**Date:** 2026-04-30

## Context

The assistant needs text-to-speech that works without network access for the default
case, but also needs to support 50+ languages for multilingual users who accept
a cloud dependency.

Evaluated alternatives: Coqui TTS (abandoned upstream), eSpeak (robotic quality),
Amazon Polly / ElevenLabs (always-cloud, per-character billing), Festival (Linux only).

## Decision

Use **Piper** as the default offline TTS engine. Piper models are downloaded once on
first use (~50–150 MB), run on CPU, and produce near-natural speech. Use the
**OpenAI TTS API** as an opt-in engine for multilingual scenarios; it supports 57
languages with a single model and has a simple streaming API already wrapped by
LiteLLM.

## Consequences

- Default path has zero network dependency after first model download.
- Multilingual users incur per-character cost only when they explicitly opt in.
- Two engine implementations must be maintained behind the `TTSEngine` abstract base.
