# 26-active-initiatives.md

**Read at every session boot.** Keep under ~80 lines. One entry per active initiative; move finished items to a one-line "Recently completed" note. (This file is the project's "active context" doc, with `29-session-handoff.md`.)

**Last updated:** 2026-07-09

---

## Active

*(none — Phase 4 + Production Hardening delivered, awaiting user direction)*

## Next up (awaiting user direction)

No further phase is defined. Candidates to discuss with the user before scoping any further work:
the Synchronization Engine (`engines/sync`, listed as "future" in `03-system-architecture.md`),
console UX polish (create/update forms, richer graph visualization beyond the current edge-list
view), or extending the auth tier (admin-only key scope, key rotation API) if a real deployment
need arises.

## Proposals / parking lot

* Additive edit to `30-memory/02-memory-schema.md` lifecycle enum (per ADR-0003) — user-owned normative doc, open since Phase 1.
* Consider `Deprecation`-header machinery when the first deprecation actually happens (not before — Simplicity Wins).
* If a real embedding model provider is ever wired in behind `EmbeddingProviderABC`, no ADR is needed to swap it — only if the *default* changes (ADR-0004).
* If routes ever adopt `response_model=` (so OpenAPI documents responses too), regenerate the TS SDK's response types from OpenAPI instead of hand-writing them — needs its own ADR (ADR-0005).
* No CI pipeline exists yet; if one is added, wire in a check that `sdk/typescript/openapi.json` isn't stale relative to `backend/mip/api/**` (ADR-0005 follow-up).
* Console has no create/update forms yet (read + lifecycle actions + Consolidate/Learn/Export-Import + search only).
* Graph is presented as an edge list (Relationships tab, per-memory) — no visual graph/network diagram yet; would need a charting dependency decision (ADR-worthy if added).
* Export/Import currently skip (never overwrite) memory_ids that already exist locally — a future "force re-import" mode would need its own invariant review (INV-ID-001).
* Rate limiting is single-process/in-memory (ADR-0007) — would need a Redis-backed limiter (its own ADR) before horizontally scaling the backend.
* No admin-only API-key tier — any valid key can call `rebuild-projections`; restrict at the network/reverse-proxy layer if needed, or design a tier system later (ADR-worthy).

## Recently completed

* 2026-07-09 — **Production Hardening** (ADR-0007): opt-in API-key auth + namespace/ownership
  isolation, opt-in rate limiting, Docker packaging (`backend/Dockerfile` + `docker-compose.yml`),
  new `22-deployment.md`. All disabled by default — zero behavior change for existing deployments.
  `mip/core/errors.py` split into a package to stay under the 300-line budget. Full stack updated
  (backend, Python/TS SDKs, CLI, console). 342/42/24 backend+SDK+CLI tests, 42 TS SDK tests
  (incl. live), 52 frontend tests, all green.
* 2026-07-09 — **Phase 4 Intelligence**: relationship graph, graph search mode, Consolidate,
  Learn, Export/Import, trust maturation, ADR-0006. All 4 client surfaces updated.
* 2026-07-08 — **Phase 3 Developer Platform**: `sdk/python` (mip_sdk), `sdk/typescript` (@mip/sdk), `cli` (Click), `frontend` console, quickstart docs + 3 runnable examples, ADR-0005.
* 2026-07-08 — **Phase 2 Retrieval & Explainability**: FTS5/sqlite-vec search, hybrid ranking, `/v1/search`, `/v1/explain`, `/v1/context`, Trust scoring, ADR-0004.
* 2026-07-07 — **Phase 1 Core Memory Engine**: event-sourced lifecycle, full CRUD/archive/restore API, ADR-0003.
* 2026-07-07 — Foundation: CLAUDE.md v2.0, memory bank docs, ADR-0001/0002.
