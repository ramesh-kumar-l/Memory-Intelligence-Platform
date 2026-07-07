# ADR-0001: Backend Stack — Python 3.12 + FastAPI + SQLite

**Status:** Accepted
**Date:** 2026-07-07
**Deciders:** Project owner (user), foundation session

## Context

The normative specs (`30-memory/*`) are deliberately implementation-agnostic; no backend language, framework, or database was chosen. MIP Core needs a concrete stack that serves: offline-first/local-first operation, event sourcing, storage independence, explainability, a worldwide contributor base, and Python as the first SDK language.

## Decision

MIP Core is implemented in **Python 3.12+** with **FastAPI** (REST transport) and **SQLite** as the default storage engine (WAL mode; FTS5 for keyword search; `sqlite-vec` for vectors in Phase 2), behind repository/event-store interfaces so alternative engines (PostgreSQL, others) can be added without touching domain code.

## Alternatives Considered

| Option | Why not chosen |
| --- | --- |
| TypeScript + Node (Fastify) | One-language stack appeal, but weaker local-AI/embedding ecosystem; Python SDK is first-class anyway |
| Kotlin + Ktor | Aligns with Android goal, but slower iteration and smaller server-side contributor pool for the core platform |
| Rust + Axum | Best raw reliability/performance, but highest cost and slowest iteration — conflicts with "Simplicity Wins" for v1 |
| PostgreSQL as default DB | Contradicts offline-first/zero-config; remains available later via the repository abstraction |

## Consequences

* Positive: zero-config local deployment; largest contributor familiarity; typed API + OpenAPI generation for free (pydantic/FastAPI); embeddings/local inference ecosystem available for Phases 2/4.
* Negative / accepted trade-offs: Python single-process throughput ceiling (acceptable for local-first core; horizontal/native paths stay open behind interfaces); SQLite single-writer model (mitigated by per-memory transition locks and WAL).
* Follow-ups: `03-system-architecture.md` and `21-coding-standards.md` encode the stack (done); Phase 1 scaffold implements it.

## Compliance Notes

Storage independence preserved via `storage/` interfaces (no SQL outside adapters). Model independence preserved via `EmbeddingProviderABC`. Offline-first: everything runs locally with no cloud dependency. API semantics remain transport-independent per the contract.
