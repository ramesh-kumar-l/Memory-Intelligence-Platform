# Architecture Document

## System Overview

MIP Core is a Python 3.12 / FastAPI service backed by SQLite, structured as a hexagonal (ports & adapters) system. Memory Objects are the single source of truth; every derived structure — full-text index, vector index, relationship graph — is a regenerable projection rebuilt deterministically from an append-only event log. Four client surfaces (React/TS console, CLI, Python SDK, TypeScript SDK) talk to one versioned REST contract; none embed business logic.

## Architecture Diagram (described)

```
Clients:  Console (React/TS) · CLI (Click, built on the Python SDK) · SDKs (Python/TS)
             │
             ▼
API Layer (backend/mip/api)        FastAPI routers, DTOs, error envelope, /v1
             │  auth dependency (opt-in, ADR-0007) + rate-limit middleware (opt-in)
             ▼
Engines (backend/mip/engines)      one package per runtime engine (orchestration only)
             │
             ▼
Core Domain (backend/mip/core)     pure, no I/O — model, state machine, invariants, errors
             │
             ▼
Events (backend/mip/events)        append-only event log, interfaces
Storage (backend/mip/storage)      repository interfaces + SQLite adapters
             │
             ▼
SQLite (event store · projections · FTS5 · sqlite-vec)
```

Dependency rule: arrows point downward only. `core` imports nothing from any other layer. Engines depend on `core` plus storage/event **interfaces**, never concrete adapters — adapters are wired at process startup via FastAPI dependency injection.

## Core Components

- **Core Domain (`mip/core`)** — the Memory Object model (Pydantic, 11 schema sections), the lifecycle state machine with a legal-transition table, `INV-*` invariant checks, and the `MIPError` hierarchy mapped to `MEM-1000..8000` error codes. Zero I/O; fully unit-testable in isolation.
- **Engines (`mip/engines`)** — one package per capability: Experience, Validation, Memory Manager (the lifecycle kernel), Semantic, Knowledge (graph), Context, Retrieval, Learning, Trust, and (future) Synchronization. Engines not yet in scope have no placeholder code — packages are created in the phase that implements them.
- **Events (`mip/events`)** — every state change is an immutable event (`event_id · memory_id · event_type · payload · actor · trace_id · sequence`). Events are never updated or deleted; corrections are new events. `rebuild_projections` replays the log to reconstruct current state deterministically (tested).
- **Storage (`mip/storage`)** — `EventStoreABC · MemoryRepositoryABC · SearchIndexABC · VectorIndexABC · BlobStoreABC`, implemented today by SQLite adapters (WAL mode, FTS5 for keyword search, sqlite-vec for embeddings). No code outside `storage/` may reference SQL directly.
- **API Layer (`mip/api`)** — versioned REST routes (`/v1/memories`, `/v1/search`, `/v1/context`, `/v1/explain`, admin), a uniform error envelope, and an opt-in auth/rate-limit layer added in the production-hardening pass (ADR-0007) as a FastAPI dependency, not middleware, so it composes per-router without touching engine code.

## Tradeoffs

| Decision | Chosen | Rejected | Why |
| --- | --- | --- | --- |
| Source of truth | Event log, projections regenerable | Mutable row-per-memory table | Replayability and auditability outweigh the extra read-path indirection (Correctness > Performance in the Constitution's priority order) |
| Storage engine | SQLite (WAL + FTS5 + sqlite-vec) | Postgres / dedicated vector DB | Offline-first, zero-config default; abstracted behind repository interfaces so it's swappable later without an ADR-mandated rewrite |
| Auth model | Static API-key → namespace map | Full identity/accounts system | Roadmap explicitly scopes identity/auth to a future Semantic Control Plane; lightweight key-based ownership isolation satisfies the *current* "MIP enforces namespace isolation" requirement without reversing that boundary (ADR-0007) |
| Rate limiting | In-memory, single-process sliding window | Redis-backed distributed limiter | SQLite's single-writer model means MIP doesn't yet assume horizontal scaling; building a distributed limiter now would be speculative complexity |

## Scaling Strategy

Current ceiling is intentionally the single-writer SQLite model: one uvicorn worker per deployment (documented in `22-deployment.md`; the Dockerfile explicitly does not set `--workers > 1`). Vertical scaling (bigger box, WAL mode's concurrent-readers benefit) covers single-tenant/local-first use well past typical personal or small-team workloads. The abstraction boundary (`storage/interfaces.py`) is the designed escape hatch: swapping in Postgres + a distributed vector store behind the same `*ABC` interfaces is the intended path to horizontal scale, gated by an ADR when that need is real rather than hypothetical.

## Reliability Strategy

Every lifecycle transition is a per-memory advisory-locked, single-writer operation (`INV-CONCUR-001`); concurrent updates create new versions rather than racing on a mutation. Enrichment/index/graph failures are explicit failure states with retry policies and never corrupt the event log — the log is the one thing that must never be wrong. `rebuild_projections` is a first-class admin operation specifically because projections must be trustworthy even after a bug in a projector: replay is the recovery mechanism, not a backup restore.
