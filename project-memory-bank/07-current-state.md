# 07-current-state.md

**Read at every session boot.** Keep under ~80 lines. Reflects reality — update before ending any session. (This file is the project's "implementation status" doc.)

**Last updated:** 2026-07-08

---

## Status: Phase 2 — Retrieval & Explainability COMPLETE (all gates green)

| Area | State |
| --- | --- |
| Specifications | ✅ Complete (`30-memory/01–06`); lifecycle enum drift resolved by ADR-0003 |
| Engineering OS | ✅ `CLAUDE.md` v2.0 + Constitution; operational docs 03/05/08/09/18/20/21 |
| Decisions | ✅ ADR-0001 Python/FastAPI/SQLite · ADR-0002 React/TS/Vite · ADR-0003 lifecycle/deletion · ADR-0004 retrieval/explainability architecture |
| Backend Phase 1 | ✅ Core domain, 11-state machine, event store, Memory Manager, REST API `/v1` CRUD+lifecycle |
| Backend Phase 2 | ✅ FTS5 keyword index, sqlite-vec semantic index, hybrid ranking, `/v1/search`, `/v1/explain`, `/v1/context`, real enrichment, basic Trust scoring |
| Tests / gates | ✅ ~276 tests green; ruff + mypy --strict clean; coverage 98.07% |
| Frontend / SDKs / CLI | ❌ Not started (Phase 3) |
| Graph / learn / export | ❌ Not started (Phase 4) |

## What works right now

Everything from Phase 1, plus: `POST /v1/search` (`mode`: keyword/semantic/hybrid, namespace filter, opaque self-contained continuation tokens), `POST /v1/explain` (confidence, dynamic freshness, provenance, evidence, and — with a query — a ranking breakdown), `POST /v1/context` (Context Package blending search relevance with each memory's own importance score). Every Create/Update now runs real enrichment (derived keywords merged into `semantics.keywords`) and basic Trust confidence derivation (blend of client input + verification_status/source_count heuristic) *after* the Phase 1 activation gate — enrichment augments valid content, it never rescues invalid input. `POST /v1/admin/rebuild-projections` now also re-derives both indexes from current Memory Objects and reports `indexed_memories`.

## Key implementation facts (for future sessions)

* New packages: `mip/providers/` (`EmbeddingProviderABC` + default `LocalHashingEmbeddingProvider`, deterministic offline feature-hashing — not deep semantic understanding), `mip/engines/{semantic,trust,retrieval,context}/`.
* Indexes (`mip/storage/sqlite/search_index.py` FTS5, `vector_index.py` sqlite-vec) are write-time side effects of Create/Update, **not** event-sourced; `rebuild_indexes()` re-derives them from live Memory Objects — deterministic because embedding is a pure function of text (ADR-0004).
* Search/Context only surface `Active` memories (Archived = "removed from active retrieval"); filtering happens at query time against the `memories` projection, so index rows are never deleted on archive/delete.
* Continuation tokens for Search/Context are self-contained (`srch:` + base64 JSON of query/mode/namespace/offset) — no server-side session state.
* `sqlite-vec` and FTS5 both confirmed working on this Python 3.14/Windows environment; `sqlite-vec` needs `[[tool.mypy.overrides]] module="sqlite_vec"` (no stubs).
* Quality gate (from `backend/`, venv `.venv`): `ruff check . ; ruff format --check . ; mypy ; pytest`.

## Last completed milestone

Phase 2 — Retrieval & Explainability, 2026-07-08 (all `09-phase-plan.md` acceptance criteria verified).

## Next milestone

Phase 3 — Developer Platform (console, SDKs, CLI). **Blocked on: user approval to begin.**

## Known issues / open questions

* `30-memory/02-memory-schema.md` still lists the old 7-state enum; needs the additive edit recorded in ADR-0003 (user-owned normative doc).
* Nothing committed to git yet; commit on request.
