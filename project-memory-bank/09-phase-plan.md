# 09-phase-plan.md

**Read this when:** starting, planning, or validating any phase or phase task.

**TL;DR:** Four phases, each with objectives, scope, docs to load, acceptance criteria, and a hard stop-gate. Never start a phase (or the next phase task) without explicit user approval. Each phase builds on the previous — no rewrites of delivered work.

---

## Phase 1 — Core Memory Engine

**Objective:** a running FastAPI service where a Memory Object can be created, validated, versioned, archived, restored, and deleted, with every transition event-sourced and replayable.

**Load:** `03-system-architecture.md`, `05-api-design.md`, `21-coding-standards.md`, `20-testing-strategy.md`, `30-memory/02-memory-schema.md`, `30-memory/03-memory-state-machine.md`, `30-memory/04-memory-invariants.md`.

**Tasks (each is a stop-gate):**

1. Repo scaffold: `backend/` layout per architecture doc, pyproject, ruff/mypy/pytest config, CI-ready.
2. Core domain: `MemoryObject` pydantic model (11 sections), required-field + range validation, structured validation errors.
3. State machine: states, legal-transition table, illegal-transition rejection, per-memory transition lock.
4. Event store: SQLite append-only events, lifecycle event types, projection rebuild (`replay ⇒ identical state`).
5. Storage: repository interfaces + SQLite adapters (no SQL outside `storage/`).
6. API: CreateMemory, GetMemory (incl. versions), UpdateMemory (new version, `If-Match`), DeleteMemory (idempotent), Archive, Restore, list, health, version; error envelope + `Idempotency-Key` middleware.
7. Tests: invariant suite (identity/state/version/concurrency groups), full transition-table tests, API contract tests.

**Out of scope:** search, embeddings, semantics enrichment (Enriching state completes trivially in Phase 1), UI, SDKs, graph, learning, sync.

**Acceptance criteria:**

* All legal transitions succeed and emit events; all illegal transitions rejected with `MEM-2xxx`.
* Replay of the event log reproduces identical projections.
* Update creates version N+1; prior versions readable and immutable; concurrent update without matching `If-Match` → `MEM-4xxx`, never silent overwrite.
* Deleted is terminal; repeated delete returns success.
* Invariant + transition + API test suites green; coverage per `20-testing-strategy.md`.
* `07-current-state.md` and `29-session-handoff.md` updated.

---

## Phase 2 — Retrieval & Explainability

**Objective:** memories are findable and every retrieval is explainable.

**Load:** `03-system-architecture.md`, `05-api-design.md`, `30-memory/05-memory-api-contract.md`, `20-testing-strategy.md`.

**Tasks:** (1) FTS5 keyword search + continuation-token pagination; (2) `EmbeddingProviderABC` + local default + `sqlite-vec` semantic search; (3) hybrid ranking; (4) `POST /v1/explain` (evidence, confidence, freshness, provenance, ranking explanation); (5) `POST /v1/context` (Context Package); (6) semantic enrichment in the Enriching state (entities/keywords minimum); (7) basic Trust scoring (confidence/freshness derivation).

**Acceptance:** every search result explainable; partial results flagged with `complete`/`continuation_token`; search modes keyword/semantic/hybrid work offline; indexes fully rebuildable from Memory Objects.

---

## Phase 3 — Developer Platform

**Objective:** any engineer can use MIP in minutes: console, CLI, SDKs.

**Load:** `18-ui-design-system.md` (console), `05-api-design.md`, `21-coding-standards.md`.

**Tasks:** (1) React/TS/Vite console — memory explorer, detail view with lifecycle timeline + trust panel, search with explanations, following the design system; (2) Python SDK; (3) TypeScript SDK; (4) CLI on the Python SDK; (5) quickstart docs + examples.

**Acceptance:** console passes the design-system checklist (a11y, keyboard nav, light/dark, explainability views); SDKs preserve contract semantics (FR-API-001) with typed errors; quickstart works end-to-end on a clean machine.

---

## Phase 4 — Intelligence

**Objective:** knowledge graph, learning, consolidation, portability.

**Load:** `03-system-architecture.md`, `30-memory/01-memory-object-model.md`, `30-memory/05-memory-api-contract.md`.

**Tasks:** (1) relationship graph (typed relationships per schema Section 5) + graph search mode; (2) Consolidate (duplicate merge via relationships, history preserved); (3) Learn (derived knowledge, evidence untouched); (4) Export/Import with validation pipeline; (5) trust maturation (verification status, source counting, evidence chains).

**Acceptance:** graph regenerable from Memory Objects; consolidation never loses history; import of an export round-trips losslessly; all Phase 1–3 suites still green.

---

## Standing Rules

* A phase is done only when its acceptance criteria pass **and** the Completion Protocol summary has been delivered **and** the user approves moving on.
* Anything discovered mid-phase that expands scope goes to `26-active-initiatives.md` as a proposal, not into the current phase.
