# ADR-0004: Retrieval & Explainability Architecture (Phase 2)

**Status:** Accepted
**Date:** 2026-07-07
**Deciders:** Project owner (user), Phase 2 kickoff ("continue with Phase 2 — Retrieval & Explainability")

## Context

Phase 2 requires keyword search, semantic search, hybrid ranking, `/v1/explain`, `/v1/context`, real
enrichment, and basic Trust scoring — fully offline, with indexes regenerable from Memory Objects
(03-system-architecture.md, 09-phase-plan.md). Several implementation choices are architectural and
need to be fixed before code is written.

## Decisions

1. **Embedding provider abstraction lives in `mip/providers/`** (new top-level package, mirrors
   `storage/`: `providers/embeddings.py` defines `EmbeddingProviderABC` (`embed(text) -> vector`,
   `dimensions`); `providers/local_embedding.py` provides the default `LocalHashingEmbeddingProvider` —
   a deterministic, offline, dependency-free feature-hashing bag-of-words embedder (hashes tokens into
   a fixed-width signed accumulator, L2-normalized). It is a lexical stand-in, not deep semantic
   understanding; the ABC lets a real model (sentence-transformers, an API-backed provider, etc.) be
   substituted at `create_app()` without touching engines (Constitution Law 8: model independence).
   Chosen over embedding directly inside `engines/semantic/` because query-time (Retrieval Engine) and
   write-time (Semantic Engine) both need the *same* provider instance — it is a cross-engine provider,
   not one engine's private detail.

2. **`sqlite-vec` and SQLite FTS5 confirmed available** in this environment (Python 3.14, Windows,
   verified by direct load test) and are used as designed in `03-system-architecture.md`. All SQL/extension
   loading stays inside `mip/storage/sqlite/` (`search_index.py`, `vector_index.py`); engines depend only
   on the new `SearchIndexABC`/`VectorIndexABC` in `storage/interfaces.py`.

3. **Indexing is a write-time side effect, not an event-sourced projection.** FTS5/vector rows are
   populated when a memory is created (once, after enrichment, before/alongside the Enriching→Indexed
   hop) and refreshed on update. They are **not** derived by replaying event payloads; `rebuild_projections`
   additionally re-derives them from the current (already-enriched) Memory Object content after event
   replay completes, satisfying "indexes fully rebuildable from Memory Objects." This keeps embedding
   deterministic-pure (same text → same vector every time) so replay-identity is unaffected.

4. **Search only surfaces `Active` memories by default** (Archived is "removed from active retrieval"
   per the contract's own description of Archive; Deleted is always excluded). Filtering happens by
   joining index hits against the `memories` projection at query time — index rows are not deleted on
   archive, only filtered, which keeps index maintenance write-only (create/update) and simple.

5. **Hybrid ranking formula:** keyword score = min-max-normalized `-bm25()` (SQLite bm25 is
   lower-is-better); semantic score = `1 / (1 + L2 distance)` from `sqlite-vec`. `hybrid = alpha *
   keyword + (1-alpha) * semantic`, `alpha` configurable (`MIP_HYBRID_KEYWORD_WEIGHT`, default 0.5).
   Documented in code as an explicit, explainable formula — no hidden black-box scoring, per the
   Explainability mandate.

6. **Trust scoring is basic and derivation-only, not gatekeeping.** `engines/trust/scoring.py`
   computes `confidence` as a blend of the client-supplied value and a heuristic derived from
   `verification_status` + `source_count` at create/update time (persisted, versioned). `freshness` is
   **not** persisted as a decaying value — it is computed dynamically at Explain/Search/Context time
   from `created_at`/`updated_at` age (exponential decay, configurable half-life), because decay is a
   function of wall-clock time and must never force new memory versions just because time passed.

7. **Search/Context continuation tokens are self-contained.** Ranking order depends on the query, not
   memory_id, so the existing `mid:`-prefixed token (Phase 1, list-only) cannot represent a resume
   position. A new `srch:`-prefixed opaque token base64-encodes `{query, mode, namespace, offset}` so
   the server holds no session state (offline/local-first) and the client need not resend original
   parameters. This is still a continuation token, not offset pagination on the public contract — the
   client never sets an offset directly.

## Alternatives Considered

| Option | Why not chosen |
| --- | --- |
| Real ML embedding model (sentence-transformers) as the only provider | Requires model download/network + heavy dependency; violates offline-first and "minimal, boring dependencies" (21-coding-standards.md) for a default. The ABC still allows plugging one in. |
| Event-sourced search/vector index (new event types) | Adds event-type surface for a purely derived, regenerable artifact; contradicts "Simplicity Wins" — indexes are explicitly documented as regenerable projections, not history. |
| Hard-delete index rows on archive | Extra write path for no correctness benefit since query-time filtering already hides them; more moving parts to keep replay-safe. |
| Raw `offset` query param for search pagination | Explicitly prohibited by `30-memory/05-memory-api-contract.md`. |

## Consequences

* Positive: fully offline by default; deterministic and replay-safe; explainable ranking with a
  documented formula; provider/storage independence preserved.
* Negative / accepted trade-offs: the default embedding is lexical-hash based, not deep semantic
  understanding — acceptable for Phase 2's "offline default," revisit if/when a real model provider is
  wired in (no ADR needed to swap providers behind the ABC; an ADR is needed only if the default
  changes).
* Follow-ups: none blocking; Phase 4's graph/consolidation work will reuse `RelationshipType` data
  already in the schema, untouched by this ADR.

## Compliance Notes

Preserves storage/model independence (Constitution Law 8), explainability mandate (Law 6), and
offline-first default (Law 7). No breaking API changes; all Phase 2 endpoints are additive.
