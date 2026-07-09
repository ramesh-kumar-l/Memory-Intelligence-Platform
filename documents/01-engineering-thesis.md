# Engineering Thesis

## Title

**Memory Deserves an Operating System, Not Another Vector Store**

## Vision

AI systems are becoming durable participants in people's work and lives, but almost every one of them forgets between sessions or bolts on a vector database and calls it "memory." MIP's thesis is that memory is infrastructure-grade: it needs a lifecycle, a source of truth, explainability, and trust semantics — the same rigor we already demand of databases and file systems, applied to what an AI system knows and why it believes it.

## Problem

Today, every AI application reimplements memory from scratch: some ad-hoc conversation buffer, a vector index bolted on for "long-term memory," and no consistent answer to *why* a piece of context was retrieved, *how confident* the system should be in it, or *what happens* when it turns out to be wrong or stale. This is duplicated, inconsistent, and — because retrieval decisions silently shape what a model says — a live trust problem, not just an engineering inconvenience.

## Why Now

Three trends converge in 2025-2026: (1) agentic AI moved from single-turn chat to long-running, multi-session workflows where statelessness is a functional bug, not a UX quirk; (2) on-device and local-first AI is now viable, so "memory as a cloud service" is no longer the only option; (3) the market has enough scar tissue from ungoverned RAG pipelines that "why did the model say that" is now a board-level question, not just a debugging concern. Memory infrastructure that treats explainability and lifecycle as first-class, not bolted-on, is arriving at the right moment rather than too early.

## Differentiation

MIP is not a vector database with a marketing layer. Three properties set it apart from the current RAG/memory-library landscape:

1. **Event-sourced lifecycle, not CRUD-over-a-table.** Every Memory Object's history is an immutable event log; current state is a replayable projection (`rebuild_projections` must be deterministic — this is a tested invariant, not a promise).
2. **Explainability as an API contract, not a debug flag.** `/v1/explain` is a first-class endpoint returning evidence, provenance, and confidence — the same question a skeptical user or auditor would ask ("why did you retrieve this, and how sure are you?") is answerable by the platform itself.
3. **Storage and model independence by construction.** No engine or route imports `sqlite3` or a specific embedding SDK directly — everything is behind `*ABC` interfaces, so the default (SQLite + local embeddings, chosen for offline-first zero-config use) is a swappable decision (ADR-0001), not a load-bearing assumption baked through the codebase.

## Long-Term Impact

If this thesis is right, "memory" becomes a layer applications consume through stable APIs the same way they consume a database today — not something every team reinvents. The compounding value is architectural: a decade-scale asset (per the Constitution's own decision priority — Correctness > Simplicity > Reliability > Maintainability > Explainability > Extensibility > Performance > DX) rather than a fast-moving application feature that gets rewritten every 18 months.
