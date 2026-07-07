# 03-system-architecture.md

**Read this when:** designing or implementing any backend module, engine, storage, or event flow.

**TL;DR:** MIP Core is a Python 3.12 / FastAPI service, event-sourced on SQLite, with a hexagonal (ports & adapters) layout. Memory Objects are the source of truth; everything else (indexes, vectors, graph) is a regenerable projection. Concrete instantiation of `30-memory/06-memory-reference-architecture.md`; stack rationale in `adr/ADR-0001-backend-stack.md` and `adr/ADR-0002-frontend-stack.md`.

---

## Layered View

```text
┌──────────────────────────────────────────────────────┐
│ Clients: Console (React/TS) · CLI · SDKs (Py/TS)     │
├──────────────────────────────────────────────────────┤
│ API Layer      backend/mip/api        FastAPI, REST  │
│                (transport binding of the contract)   │
├──────────────────────────────────────────────────────┤
│ Engines        backend/mip/engines    orchestration  │
├──────────────────────────────────────────────────────┤
│ Core Domain    backend/mip/core       pure, no I/O   │
│                model · schema · state machine ·      │
│                invariants · errors                   │
├──────────────────────────────────────────────────────┤
│ Events         backend/mip/events     append-only    │
│ Storage        backend/mip/storage    repositories   │
├──────────────────────────────────────────────────────┤
│ SQLite (event store, projections, FTS5, sqlite-vec)  │
└──────────────────────────────────────────────────────┘
```

Dependency rule: arrows point downward only. `core` imports nothing from other layers. Engines depend on `core` + storage/event **interfaces**, never on concrete adapters (wired at startup via dependency injection through FastAPI).

## Module Layout

```text
backend/
├── pyproject.toml
├── mip/
│   ├── api/            # FastAPI routers, request/response DTOs, error envelope
│   │   ├── v1/         # /v1 routes: memories, search, context, explain, admin
│   │   └── middleware/ # request_id, tracing, version negotiation, idempotency
│   ├── core/           # PURE domain logic — no I/O, fully unit-testable
│   │   ├── model.py    # MemoryObject (pydantic, 11 schema sections)
│   │   ├── states.py   # lifecycle states + legal-transition table
│   │   ├── invariants.py  # INV-* checks
│   │   └── errors.py   # MIPError hierarchy ↔ MEM-1000..8000 codes
│   ├── engines/        # one package per runtime engine (see mapping below)
│   ├── events/         # event types, event store interface, projection rebuilders
│   ├── storage/        # repository interfaces + sqlite/ adapters
│   └── config.py       # settings (pydantic-settings), storage paths
└── tests/              # mirrors mip/ layout; see 20-testing-strategy.md
```

## Engine Mapping (reference architecture → implementation)

| # | Engine (spec) | Package | Phase |
| - | --- | --- | - |
| 1 | Experience Engine | `engines/experience` | 1 |
| 2 | Validation Engine | `engines/validation` | 1 |
| 3 | Memory Manager (kernel) | `engines/memory_manager` | 1 |
| 4 | Semantic Engine | `engines/semantic` | 2 |
| 5 | Knowledge Engine | `engines/knowledge` | 4 |
| 6 | Context Engine | `engines/context` | 2 |
| 7 | Retrieval Engine | `engines/retrieval` | 2 |
| 8 | Learning Engine | `engines/learning` | 4 |
| 9 | Trust Engine | `engines/trust` | 2 (basic) / 4 (mature) |
| 10 | Synchronization Engine | `engines/sync` | future |
| 11 | Event Store | `events/` | 1 |
| 12 | Query Engine | `engines/retrieval/query` | 2 |

Engines not yet in scope get no placeholder code — packages are created in the phase that implements them (Simplicity Wins).

## Event Sourcing Model

* Every state change is an immutable event appended to the `events` table (SQLite, WAL mode): `event_id (UUID) · memory_id · event_type · payload (JSON) · actor · trace_id · created_at · sequence (monotonic)`.
* Event types follow the state machine spec: `MemoryCreated`, `MemoryValidated`, `MemoryIndexed`, `MemoryActivated`, `MemoryUpdated`, `MemoryArchived`, `MemoryDeleted` (+ failure events).
* Current state (the `memories` projection table) is rebuilt deterministically by replaying events; a `rebuild_projections` admin operation must always produce identical state (FR-LIFE-004, replayability).
* Events are never updated or deleted. Corrections are new events.

## Storage Abstraction

```text
storage/interfaces.py   EventStoreABC · MemoryRepositoryABC · SearchIndexABC · VectorIndexABC · BlobStoreABC
storage/sqlite/         SqliteEventStore · SqliteMemoryRepository · Fts5SearchIndex · SqliteVecIndex · FileBlobStore
```

* SQLite is the default engine (offline-first, zero-config). PostgreSQL or others may be added later behind the same interfaces — **no code outside `storage/` may import `sqlite3` or reference SQL**.
* Vectors: `sqlite-vec` (Phase 2), embedder behind a `EmbeddingProviderABC` (model independence — no hardcoded provider).
* Graph: modeled as relationship rows in SQLite first (Phase 4); Neo4j/RDF adapters only if scale demands (requires ADR).

## Runtime Flows (canonical)

* **Create:** API → Validation Engine → Memory Manager → `MemoryCreated` event → lifecycle pipeline (Validating → Validated → Enriching → Indexed → GraphLinked → Active) with an event per transition.
* **Retrieve:** API → Retrieval Engine → Query Engine → repositories/indexes → ranked results + Explain payload (evidence, confidence, provenance) — explainability is not optional.
* **Update:** never mutates; Memory Manager creates version N+1 (`Updating → Active`), previous versions remain immutable.

## Cross-Cutting Rules

* **Concurrency:** one lifecycle transition at a time per memory (per-memory advisory lock); concurrent updates create versions, never overwrite (INV-CONCUR-001).
* **Observability:** every request carries `request_id`/`trace_id`; every transition and API call emits structured logs; sensitive payloads are never logged.
* **Failure isolation:** enrichment/index/graph failures are explicit failure states with retry policies; they never corrupt the event log.
* **Security boundary:** governance/privacy/policy belong to the Semantic Control Plane (out of MIP core scope); MIP enforces ownership and namespace isolation only.

## Frontend & Clients

* `frontend/` — React + TypeScript + Vite developer console (see `18-ui-design-system.md`), talks only to the public REST API.
* `sdk/python`, `sdk/typescript` — thin typed clients over REST, preserving contract semantics (FR-API-001). CLI is built on the Python SDK.

Changes to anything in this document that affects storage, lifecycle, events, or public APIs require an ADR.
