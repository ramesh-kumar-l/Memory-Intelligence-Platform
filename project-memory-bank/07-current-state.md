# 07-current-state.md

**Read at every session boot.** Keep under ~80 lines. Reflects reality — update before ending any session. (This file is the project's "implementation status" doc.)

**Last updated:** 2026-07-09

---

## Status: Phase 4 — Intelligence COMPLETE (all gates green)

| Area | State |
| --- | --- |
| Specifications | ✅ Complete (`30-memory/01–06`); lifecycle enum drift resolved by ADR-0003 |
| Engineering OS | ✅ `CLAUDE.md` v2.0 + Constitution; operational docs 03/05/08/09/18/20/21 |
| Decisions | ✅ ADR-0001..0005 (stack, lifecycle, retrieval, dev platform) · ADR-0006 intelligence architecture |
| Phase 1 — Core | ✅ Domain model, 11-state machine, event store, Memory Manager, REST CRUD+lifecycle |
| Phase 2 — Retrieval | ✅ FTS5/sqlite-vec, hybrid ranking, `/v1/search`, `/v1/explain`, `/v1/context`, Trust scoring |
| Phase 3 — Dev Platform | ✅ Python/TS SDKs, CLI, React console |
| Phase 4 — Graph | ✅ Relationship-graph projection (`SqliteGraphIndex`), graph search mode, `/v1/memories/{id}/relationships` |
| Phase 4 — Consolidate | ✅ `ConsolidateEngine` — merges duplicates via `duplicate_of` relationship + archive; history preserved |
| Phase 4 — Learn | ✅ `LearnEngine` — non-destructive semantic union + trust maturation, one version bump |
| Phase 4 — Trust maturation | ✅ Evidence append-only chains, source counting, verification-status thresholds |
| Phase 4 — Export/Import | ✅ `/v1/export`, `/v1/import`; validated per-memory, round-trip verified losslessly |
| Tests / gates | ✅ Backend 97.5% (321 tests) · sdk/python 98.9% (38) · cli 93.4% (21) · sdk/typescript (45 incl. live) · frontend (51) — all ruff/mypy/eslint/tsc clean |

## What works right now

Everything from Phases 1-3, plus: a relationship graph fully regenerable from Memory
Objects (`GraphEngine.rebuild()`, exercised by `POST /v1/admin/rebuild-projections`); a
`graph` search mode (`POST /v1/search {mode:"graph", query:"<seed memory_id>"}`, score =
`1/hop_distance`); `POST /v1/consolidate` (merge duplicates, nothing deleted); `POST
/v1/learn` (derived semantics + optional evidence maturation, supports
`Idempotency-Key`); `POST /v1/export` + `POST /v1/import` (backup/migration, validated
before write, per-memory atomic). All four operations are exposed through the Python SDK,
TypeScript SDK, CLI (`mip consolidate|learn|export|import`, `mip memories
relationships`), and the console (new **Intelligence** page; Memory detail's
Relationships tab now shows inbound + outbound edges; Search page has a Graph mode).

## Key implementation facts (for future sessions)

* Graph is a SQLite adjacency table (`memory_relationship_edges`), populated by
  `RetrievalEngine.index_memory()` (single choke point, same as search/vector indexes) —
  `memory_manager/engine.py` was **not** modified for any Phase 4 feature.
* Consolidate/Import add new event types (`MemoryConsolidated`, `MemoryImported`,
  `MemoryVersionImported`) but reuse existing repository methods (`create`,
  `publish_version`, `set_state`) — no new SQL beyond the graph table + `consolidation_count` column.
* `consolidation_count` and `source_count` (`UpdateMemorySpec`/`UpdateMemoryRequest`) were
  the two small additive gaps found and fixed mid-phase (see ADR-0006 + session handoff).
* Export/Import fidelity target is "what `GetMemory`/`ListVersions` already return," not
  the raw event log — verified end-to-end (engine tests, API tests, live SDK/CLI/curl runs).
* New error codes: `MEM-1008` (invalid consolidation request), `MEM-1009` (malformed
  import bundle), `MEM-2005` (consolidation target not Active) — registry stays append-only.

## Last completed milestone

Phase 4 — Intelligence, 2026-07-09 (09-phase-plan.md acceptance criteria met: graph
regenerable from Memory Objects, consolidation never loses history, export→import
round-trips losslessly — all verified by dedicated tests plus a live end-to-end run).

## Next milestone

No Phase 5 is defined in `09-phase-plan.md` — the four-phase roadmap is complete.
**Blocked on: user direction** for what comes next (hardening/production-readiness pass,
sync engine, or a new phase to scope).

## Known issues / open questions

* `30-memory/02-memory-schema.md` still lists the old 7-state enum; needs the additive
  edit recorded in ADR-0003 (user-owned normative doc, open since Phase 1).
* Nothing committed to git this session; commit on request.
