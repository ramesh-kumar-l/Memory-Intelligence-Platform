# ADR Collection

Distilled from the 7 accepted ADRs in `project-memory-bank/adr/`. Full text is normative there; this is the leverage-optimized summary for readers who won't open all 7 files.

## ADR-0001 — Backend Stack: Python / FastAPI / SQLite

**Decision:** Python 3.12 + FastAPI + SQLite (WAL, FTS5, sqlite-vec), behind a repository abstraction.
**Alternatives:** Node/TypeScript backend; Postgres-from-day-one; a dedicated vector database (Qdrant/Weaviate/pgvector).
**Rationale:** Offline-first/zero-config is a product requirement, not a nice-to-have (Vision.md: "local-first, offline-first, user-controlled synchronization"); SQLite satisfies that with no operational dependency. FastAPI gives typed request/response DTOs and OpenAPI generation for free, which both SDKs depend on.
**Consequences:** Single-writer ceiling (accepted, documented); storage independence preserved only if engines never bypass the repository interfaces — enforced as a standing architectural rule, not just a convention.

## ADR-0002 — Frontend Stack: React / TypeScript / Vite

**Decision:** React + TypeScript + Vite for the developer console.
**Alternatives:** Svelte/SolidJS (smaller runtime); server-rendered console (Next.js).
**Rationale:** Console is explainability-first tooling for developers, not a marketing site — React's ecosystem maturity and Vite's dev-loop speed outweighed bundle-size concerns for this audience.
**Consequences:** Console has no SSR/SEO surface — acceptable since it's an authenticated developer tool, not public-facing content.

## ADR-0003 — Lifecycle States and Deletion Semantics

**Decision:** Explicit lifecycle state machine with a legal-transition table; deletion is a tombstone state, not a row removal; Delete/Archive/Restore are idempotent.
**Alternatives:** Soft-delete flag on a mutable row; hard delete with a separate audit log.
**Rationale:** Event sourcing requires every transition to be representable as an event; a boolean `is_deleted` flag can't express "deleted, then restored, then deleted again" as a coherent history.
**Consequences:** Idempotency on already-Deleted memories became a real constraint later — it's the reason ADR-0007 needed `peek_namespace()` instead of reusing `get_memory()` for auth checks.

## ADR-0004 — Retrieval & Explainability Architecture

**Decision:** Hybrid retrieval (FTS5 keyword + sqlite-vec semantic), fused ranking, `/v1/explain` as a dedicated endpoint returning evidence/provenance/confidence; basic Trust metadata introduced here, matured in ADR-0006.
**Alternatives:** Semantic-only retrieval; explainability as response metadata bolted onto search results instead of its own endpoint.
**Rationale:** Keyword recall catches what embeddings miss (exact identifiers, names); a dedicated `/explain` endpoint keeps the "why" answerable independent of "what," so explainability doesn't get silently dropped from a future response-shape change.
**Consequences:** Two indexes to keep consistent with the event log — solved by treating both as regenerable projections, same as everything else.

## ADR-0005 — Developer Platform Architecture

**Decision:** Python SDK, TypeScript SDK, and CLI (built on the Python SDK, not a separate implementation), console consuming the public REST API only.
**Alternatives:** CLI as its own direct-to-API client; generate both SDKs from OpenAPI immediately.
**Rationale:** A CLI built on the SDK guarantees the SDK is dogfooded by the first "real" consumer; hand-writing the TS SDK's response types (deferred OpenAPI-codegen decision) was accepted as a known follow-up, not a defect.
**Consequences:** Parking-lot item: if routes ever adopt `response_model=`, regenerate TS types from OpenAPI instead of hand-writing them (needs its own ADR).

## ADR-0006 — Intelligence Architecture

**Decision:** Relationship graph modeled as rows in SQLite (not a dedicated graph database) for Phase 4; Consolidate/Learn/Import/Export with per-memory-atomic, whole-bundle-partial semantics; trust maturation.
**Alternatives:** Neo4j/RDF graph store; whole-bundle-atomic import (all-or-nothing).
**Rationale:** Graph scale doesn't yet justify a dedicated store (Simplicity Wins); partial-import semantics let a bundle with one bad entry still deliver the other N-1 rather than failing the whole operation.
**Consequences:** This per-entry-rejection pattern became the template ADR-0007 reused for namespace-violating import entries — a direct example of an ADR's precedent shaping a later, unrelated decision.

## ADR-0007 — Production Hardening

**Decision:** Opt-in API-key → namespace map for auth (not an identity/accounts system); auth as a FastAPI dependency, not middleware; opt-in single-process in-memory rate limiting; single-worker Docker packaging.
**Alternatives:** Full identity/accounts/RBAC system; JWT-based auth; Redis-backed distributed rate limiter; multi-worker Docker image.
**Rationale:** `08-roadmap.md` explicitly scopes identity/auth out of MIP core (owned by a future Semantic Control Plane) — this ADR exists *because* that conflict was caught before implementation started, not discovered after. The lightweight key→namespace map satisfies "MIP enforces ownership and namespace isolation" (an existing architectural claim) without building the accounts system the roadmap defers.
**Consequences:** Every new setting defaults to disabled, preserving zero-config behavior for the 321 pre-existing tests and any existing deployment; `mip/core/errors.py` had to be split into a package (`errors/base.py` + `errors/factories.py`) to stay under the 300-line file budget after adding 5 new error codes — a direct, traceable consequence of a hard engineering constraint meeting a feature addition.
