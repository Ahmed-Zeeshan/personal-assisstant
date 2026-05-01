# 0005 — LiteLLM as the LLM Abstraction Layer

**Status:** Accepted  
**Date:** 2026-04-30

## Context

The assistant must support multiple LLM providers (Anthropic Claude, OpenAI GPT,
Google Gemini, local Ollama) with a unified tool-use interface. Writing per-provider
adapters is maintenance-heavy as APIs evolve.

Options evaluated: direct SDK per provider (4 dependencies, diverging interfaces),
LangChain (heavy, many transitive deps, abstraction leaks), Haystack (ETL-oriented,
not tool-call focused).

## Decision

Use **LiteLLM** as a single shim that maps all providers to the OpenAI
`chat/completions` schema. Tool call requests and responses use the OpenAI JSON
format regardless of the underlying provider.

## Consequences

- Single `brain.py` works across all four providers.
- LiteLLM version bumps occasionally introduce breaking changes — pin minor versions
  in CI.
- Local Ollama support is free; users need no cloud key for a fully local setup.
