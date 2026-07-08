# 26-active-initiatives.md

**Read at every session boot.** Keep under ~80 lines. One entry per active initiative; move finished items to a one-line "Recently completed" note. (This file is the project's "active context" doc, with `29-session-handoff.md`.)

**Last updated:** 2026-07-08

---

## Active

*(none — Phase 3 delivered, awaiting phase gate)*

## Next up (awaiting user approval)

**Phase 4 — Intelligence.** Scope and acceptance criteria in `09-phase-plan.md`: relationship graph + graph search mode, Consolidate (duplicate merge, history preserved), Learn (derived knowledge, evidence untouched), Export/Import with validation pipeline, trust maturation (verification status, source counting, evidence chains). Load: `03-system-architecture.md`, `30-memory/01-memory-object-model.md`, `30-memory/05-memory-api-contract.md`.

## Proposals / parking lot

* Additive edit to `30-memory/02-memory-schema.md` lifecycle enum (per ADR-0003) — user-owned normative doc.
* Consider `Deprecation`-header machinery when the first deprecation actually happens (not before — Simplicity Wins).
* If a real embedding model provider is ever wired in behind `EmbeddingProviderABC`, no ADR is needed to swap it — only if the *default* changes (ADR-0004).
* If routes ever adopt `response_model=` (so OpenAPI documents responses too), regenerate the TS SDK's response types from OpenAPI instead of hand-writing them — needs its own ADR since it changes response serialization behavior (ADR-0005).
* No CI pipeline exists yet; if one is added, wire in a check that `sdk/typescript/openapi.json` isn't stale relative to `backend/mip/api/**` (ADR-0005 follow-up).
* Console has no create/update forms yet (read + lifecycle-action + search only) — add if users need to author memories from the UI rather than SDK/CLI.

## Recently completed

* 2026-07-08 — **Phase 3 Developer Platform**: `sdk/python` (mip_sdk), `sdk/typescript` (@mip/sdk, OpenAPI-generated request types), `cli` (Click, on mip_sdk), `frontend` console (React/TS/Vite — Memories/Search/Settings pages, design-system components), quickstart docs + 3 runnable examples verified against a live backend, ADR-0005. 30+16+29+45 tests across the four new packages, all green.
* 2026-07-08 — **Phase 2 Retrieval & Explainability**: FTS5 keyword search, sqlite-vec semantic search, hybrid ranking, `/v1/search`, `/v1/explain`, `/v1/context`, real enrichment, basic Trust scoring, ADR-0004. ~276 tests, 98.07% coverage.
* 2026-07-07 — **Phase 1 Core Memory Engine**: `backend/` service, event-sourced lifecycle, full CRUD/archive/restore API, ADR-0003.
* 2026-07-07 — Foundation: CLAUDE.md v2.0, memory bank docs, ADR-0001/0002.
