# 29-session-handoff.md

**Read at every session boot.** Overwritten at the end of every session; keep under ~80 lines.

**Session date:** 2026-07-08 (session 3)

---

## What this session did

Implemented **Phase 2 — Retrieval & Explainability** end to end in `backend/` (user approved the phase and asked for the full scope in one pass, as with Phase 1):

1. ADR-0004: embedding provider abstraction, FTS5/sqlite-vec index design, hybrid ranking formula, trust scoring formulas, self-contained search continuation tokens — verified `sqlite-vec` and FTS5 both work on this Python 3.14/Windows setup before committing to the design.
2. `mip/providers/`: `EmbeddingProviderABC` + default `LocalHashingEmbeddingProvider` (deterministic offline feature-hashing, no ML deps/network).
3. Storage: `SearchIndexABC`/`VectorIndexABC` + `Fts5SearchIndex`/`SqliteVecVectorIndex` adapters; `Database` now loads the `sqlite-vec` extension and owns the FTS5/vec0 schema.
4. Engines: `engines/semantic` (keyword/entity enrichment), `engines/trust` (confidence blend + dynamic freshness decay), `engines/retrieval` (indexing + keyword/semantic/hybrid search + ranking + explain support), `engines/context` (BuildContext).
5. `MemoryManager` extended (not rewritten): enrichment + trust scoring run **after** the Phase 1 activation gate (additive only — never rescues invalid input); indexing happens at create/update; `rebuild_projections` now also re-derives both indexes and reports `indexed_memories`.
6. API: `POST /v1/search`, `POST /v1/explain`, `POST /v1/context` + DTOs; self-contained `srch:` continuation tokens (`api/v1/pagination.py`, `retrieval_common.py`).
7. Tests (~276 total, all green): providers, engines (semantic/trust/retrieval/context), storage adapters (FTS5/vector), API contract tests for all three new endpoints, MemoryManager integration tests for enrichment/indexing/rebuild.

## Decisions made

* **ADR-0004** (accepted) — see above; key point: indexes are write-time side effects re-derivable from Memory Objects, not event-sourced.
* Enrichment order fixed mid-session: originally ran enrichment *before* `check_activation`, which silently let content with empty `semantics` pass (auto-derived keywords satisfied INV-SEM-001). Reordered so `check_activation` always runs on caller-supplied content first — preserves the Phase 1 contract exactly; enrichment is purely additive afterward.
* Keywords accumulate across versions by design (`UpdateMemorySpec`: "absent fields keep prior values" — Phase 1, unchanged); a title-only update does not purge previously-derived keywords. Documented via test naming, not treated as a bug.

## Next steps

1. User reviews Phase 2 (gates: `backend/` → `ruff check . ; ruff format --check . ; mypy ; pytest`).
2. Optionally commit (nothing committed yet).
3. On approval: **Phase 3 — Developer Platform** (console, Python/TS SDKs, CLI). Load `18-ui-design-system.md`, `05-api-design.md`, `21-coding-standards.md`.

## Open questions (need user input)

1. Approve Phase 3 start?
2. Who edits `30-memory/02-memory-schema.md` state enum (still open from Phase 1/ADR-0003)?

## Watch out for

* Keep every source file < 300 lines. Largest is `engines/memory_manager/engine.py` (~286) — split before extending further.
* `LocalHashingEmbeddingProvider` is a lexical stand-in, not real semantic understanding; swapping in a real model provider needs no ADR (ADR-0004), only if the *default* changes.
* `sqlite-vec` needs `[[tool.mypy.overrides]] module="sqlite_vec"` in `pyproject.toml` (no type stubs).
* Test `db`/`embeddings` fixtures share `TEST_EMBEDDING_DIMENSIONS = 32` in `conftest.py` — the vec0 table dimension is fixed at `Database` construction, so any fixture using a different provider dimension will break.
