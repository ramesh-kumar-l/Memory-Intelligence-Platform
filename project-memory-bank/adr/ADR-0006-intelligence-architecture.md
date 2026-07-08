# ADR-0006: Intelligence Architecture — Graph, Consolidate, Learn, Export/Import, Trust Maturation (Phase 4)

**Status:** Accepted
**Date:** 2026-07-08
**Deciders:** Project owner (user), Phase 4 kickoff ("continue with Phase 4 — Intelligence")

## Context

Phase 4 requires: a relationship graph + graph search mode, Consolidate (duplicate merge, history
preserved), Learn (derived knowledge, evidence untouched), Export/Import with a validation pipeline,
and trust maturation (verification status, source counting, evidence chains) — all regenerable from
Memory Objects, all event-sourced, none rewriting Phase 1-3 code (09-phase-plan.md, Stability Before
Refactoring). `RelationshipType` (including `duplicate_of`) and `Lifecycle.consolidation_count` already
exist in the schema (Phase 1) and needed no changes.

## Decisions

1. **Graph is a regenerable adjacency projection, not a new storage engine.** `GraphIndexABC` /
   `SqliteGraphIndex` (new `memory_relationship_edges` table) store one row per relationship, indexed
   by both `memory_id` (source) and `target_memory_id`, so neighbor lookups work in either direction
   even though `Relationship` is stored directionally on the source only. `GraphEngine`
   (`engines/knowledge/graph.py`) owns BFS traversal (`neighbor_hops`) and is rebuildable from live
   Memory Objects alone (`rebuild()`), mirroring `RetrievalEngine.rebuild_indexes()`.

2. **`RetrievalEngine` composes `GraphEngine`, not `MemoryManager`.** `RetrievalEngine.index_memory()`
   (the existing single choke-point `MemoryManager` already calls after every create/update) now also
   calls `graph.index_memory()`. This adds zero new call sites in `memory_manager/engine.py` — the most
   stable, most heavily-tested file in the codebase stays untouched. Engine-to-engine composition below
   `MemoryManager` is a new pattern but a narrow one (one collaborator, one call site).

3. **Graph is a fourth search mode reusing the existing `query` slot as the seed `memory_id`.**
   `POST /v1/search {mode: "graph", query: "<memory_id>"}` — no new request field, no new continuation-
   token variant. Score = `1 / hop_distance` (hop 1 = 1.0, hop 2 = 0.5, ...), an explicit, explainable
   formula consistent with ADR-0004's ranking style. Rejected a dedicated `seed_memory_id` field as
   unnecessary API surface growth for what is, structurally, still "the string that identifies what to
   search from."

4. **Consolidate is pure orchestration over existing `MemoryManager` methods, not a new lifecycle
   path.** `ConsolidateEngine.consolidate(primary_id, duplicate_ids, ...)` calls `update_memory` on each
   duplicate (adds a `duplicate_of` relationship → new version, existing versioning/event machinery) then
   `archive_memory` on it (existing, idempotent). Nothing is deleted; every step already emits its own
   audit event. A new `MemoryConsolidated` event (payload: primary + duplicate id) increments the
   primary's `consolidation_count` — the one piece of state with no existing write path. This guarantees
   "consolidation never loses history" by construction: the only two mutating primitives it uses
   (version-bump, archive) already preserve history.

5. **`consolidation_count` becomes a live-overlaid `MemoryRecord` column**, exactly like
   `state`/`archived_at`/`deleted_at` already are in `get_object()`. Consistent with the established
   overlay pattern (frozen version snapshot + live projection fields), not a special case.

6. **Learn reuses `update_memory` for both semantic learning and trust maturation in one version
   bump.** `LearnEngine.learn()` unions caller-supplied `derived` semantics into the existing tuple
   fields (same non-destructive union strategy as `enrichment.py`'s keyword merge — INV-SEM-002: never
   invalidates prior semantic content) and, when `new_evidence`/`verifier` are supplied, calls
   `TrustEngine.mature_evidence()` to *append* evidence (INV-TRUST-003: old evidence remains
   accessible), bump `source_count`, and recompute `verification_status` via an explicit threshold table
   (`source_count >= 3` → `Verified`, `>= 2` → `PartiallyVerified`, else unchanged) before re-deriving
   confidence through the existing `derive_confidence`. One `UpdateMemorySpec`, one version, one audit
   event — Learn never touches `trust.evidence` destructively and never calls anything but
   `update_memory`.

7. **Trust maturation has no dedicated endpoint.** `05-api-design.md`'s Phase 4 endpoint table lists
   only Consolidate/Learn/Export/Import. Folding maturation into Learn (decision 6) delivers the
   capability without adding undocumented API surface — additive-but-unlisted endpoints would need their
   own contract update; reusing Learn needs none.

8. **Export/Import round-trip fidelity target is "what `GetMemory` already returns," not the raw
   append-only event log.** Export walks, per memory, every version via the same `get_object(id,
   version=v)` overlay logic already exposed through `GET /v1/memories/{id}?version=v`, plus the record's
   live state — i.e., exactly what a client can already observe, not new internal fidelity guarantees.
   Import validates every version of every memory against schema + `activation_violations` (the
   validation pipeline the contract requires) before writing anything for that memory, then replays it
   through two new event types: `MemoryImported` (version 1, reuses `repository.create()` semantics) and
   `MemoryVersionImported` (version N, reuses `repository.publish_version()` + a `set_state()` call to
   restore the exact original state, since `publish_version` itself always lands on `Active`). No new
   repository methods were needed — only two new event types and two new `projector.apply_event`
   branches, reusing existing repository calls.

9. **Import is atomic per-memory, not atomic across the whole bundle.** Each memory's full version
   chain is written in one transaction; one memory's validation failure is reported (`rejected`) without
   blocking the rest of the bundle — consistent with the existing partial-results pattern
   (`warnings[]`/`complete` on Search). A `memory_id` that already exists in the target store is skipped
   and reported (`skipped`), never overwritten — importing into a non-empty store must never violate
   INV-ID-001 (identity uniqueness) or silently clobber local history.

## Alternatives Considered

| Option | Why not chosen |
| --- | --- |
| Dedicated graph database/adapter (Neo4j) | `03-system-architecture.md` explicitly defers this until scale demands it (requires its own ADR); SQLite adjacency table is sufficient at local-first scale. |
| New `seed_memory_id` field on `SearchRequest` for graph mode | Extra schema surface for a mode that only ever needs one identifier; reusing `query` keeps the request/response/pagination shape identical across all four modes. |
| Full event-sourced replay of the 6-state creation pipeline for Import | Import materializes already-lifecycled data (backups/migrations), not raw new input; forcing it through `Created → ... → Active` would fabricate a false audit history and require re-running validation semantics that don't apply to historical states like `Archived`/`Deleted`. |
| Whole-bundle-atomic Import | One bad memory in a 10,000-memory backup would reject the entire restore; per-memory atomicity with a reported `rejected` list is the practical, still-invariant-safe choice. |
| New `/v1/memories/{id}/verify` endpoint for trust maturation | Not in the contract's Phase 4 endpoint table; folding into Learn avoids inventing unauthorized API surface. |

## Consequences

* Positive: zero changes to `memory_manager/engine.py`; all five Phase 4 capabilities are additive
  (new tables, new event types, new engines, new routes) with no modification to Phase 1-3 request/
  response shapes; graph/consolidate/learn/import are all fully event-sourced and replayable
  (INV-CONS-004); export/import round-trips exactly what the public API already exposes.
* Negative / accepted trade-offs: graph search score is a simple hop-distance heuristic, not a weighted
  path-quality score — acceptable per the Explainability mandate (simple beats accurate-but-opaque);
  Import re-creating a previously-deleted `memory_id` is possible only when the target store has no
  existing row for that id (never on top of a live one), matching INV-STATE-003's spirit (no
  Deleted→Active resurrection) while still allowing legitimate backup restores into an empty store.
* Follow-ups: none blocking. If Export/Import is later asked to preserve the *exact* original event log
  (not just the version chain), that needs its own ADR.

## Compliance Notes

Preserves storage/model independence (Constitution Law 8: graph is one more `storage/` adapter behind
an ABC), explainability (Law 6: every graph/consolidate/learn/trust score has a documented formula),
and "events are immutable, state is a projection of history" (Law 5). No breaking changes to any
Phase 1-3 endpoint; all Phase 4 endpoints are net-new additions to `05-api-design.md`'s already-approved
endpoint table.
