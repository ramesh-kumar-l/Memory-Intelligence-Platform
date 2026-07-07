# 26-active-initiatives.md

**Read at every session boot.** Keep under ~80 lines. One entry per active initiative; move finished items to a one-line "Recently completed" note. (This file is the project's "active context" doc, with `29-session-handoff.md`.)

**Last updated:** 2026-07-07

---

## Active

*(none — Phase 1 delivered, awaiting phase gate)*

## Next up (awaiting user approval)

**Phase 2 — Retrieval & Explainability.** Scope and acceptance criteria in `09-phase-plan.md`: FTS5 keyword search, `EmbeddingProviderABC` + sqlite-vec semantic search, hybrid ranking, `POST /v1/explain`, `POST /v1/context`, real enrichment in the Enriching state, basic Trust scoring. Load: `03`, `05`, `30-memory/05`, `20`.

## Proposals / parking lot

* Additive edit to `30-memory/02-memory-schema.md` lifecycle enum (per ADR-0003) — user-owned normative doc.
* Consider `Deprecation`-header machinery when the first deprecation actually happens (not before — Simplicity Wins).

## Recently completed

* 2026-07-07 — **Phase 1 Core Memory Engine**: `backend/` service, event-sourced lifecycle, full CRUD/archive/restore API, 208 tests, 98% coverage, ADR-0003.
* 2026-07-07 — Foundation: CLAUDE.md v2.0, memory bank docs, ADR-0001/0002.
