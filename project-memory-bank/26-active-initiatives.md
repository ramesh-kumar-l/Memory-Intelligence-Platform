# 26-active-initiatives.md

**Read at every session boot.** Keep under ~80 lines. One entry per active initiative; move finished items to a one-line "Recently completed" note. (This file is the project's "active context" doc, with `29-session-handoff.md`.)

**Last updated:** 2026-07-08

---

## Active

*(none — Phase 2 delivered, awaiting phase gate)*

## Next up (awaiting user approval)

**Phase 3 — Developer Platform.** Scope and acceptance criteria in `09-phase-plan.md`: React/TS/Vite console (memory explorer, lifecycle timeline, trust/explain panels per `18-ui-design-system.md`), Python SDK, TypeScript SDK, CLI on the Python SDK, quickstart docs + examples. Load: `18-ui-design-system.md`, `05-api-design.md`, `21-coding-standards.md`.

## Proposals / parking lot

* Additive edit to `30-memory/02-memory-schema.md` lifecycle enum (per ADR-0003) — user-owned normative doc.
* Consider `Deprecation`-header machinery when the first deprecation actually happens (not before — Simplicity Wins).
* If a real embedding model provider is ever wired in behind `EmbeddingProviderABC`, no ADR is needed to swap it — only if the *default* changes (ADR-0004).

## Recently completed

* 2026-07-08 — **Phase 2 Retrieval & Explainability**: FTS5 keyword search, sqlite-vec semantic search, hybrid ranking, `/v1/search`, `/v1/explain`, `/v1/context`, real enrichment, basic Trust scoring, ADR-0004. ~276 tests, 98.07% coverage.
* 2026-07-07 — **Phase 1 Core Memory Engine**: `backend/` service, event-sourced lifecycle, full CRUD/archive/restore API, ADR-0003.
* 2026-07-07 — Foundation: CLAUDE.md v2.0, memory bank docs, ADR-0001/0002.
