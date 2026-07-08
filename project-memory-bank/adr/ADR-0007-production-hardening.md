# ADR-0007: Production Hardening — API-Key Auth, Rate Limiting, Deployment Packaging

**Status:** Accepted
**Date:** 2026-07-09
**Deciders:** Project owner (user), production-hardening kickoff; auth-scope conflict resolved via
explicit user choice ("Lightweight API-key auth") after the assistant flagged a documented conflict.

## Context

`08-roadmap.md` lists "identity/auth and billing" as **out of scope** for MIP core, owned by a future
Semantic Control Plane; `03-system-architecture.md` states MIP "enforces ownership and namespace
isolation only." A full identity/auth system (accounts, sessions, RBAC) would reverse that documented
boundary and requires a roadmap change, not just an ADR. The user was asked and chose the narrowest
option that still satisfies "ownership and namespace isolation": static API-key gating, no accounts.
This ADR also covers rate limiting and deployment packaging, neither of which conflicts with any
documented scope (M5 "Production Readiness" already anticipates hardening + packaging).

## Decisions

1. **Auth is a static, config-mapped API-key gate — not an identity system.** `MIP_API_KEYS` (JSON:
   `{"<key>": ["<namespace>", ...]}`, `["*"]` = unrestricted) maps opaque keys to allowed namespaces.
   No accounts, sessions, password storage, or RBAC. This is deliberately the smallest change that
   satisfies "MIP enforces ownership and namespace isolation only" without touching the identity/auth
   boundary reserved for the Semantic Control Plane.

2. **Auth and rate limiting are opt-in (`MIP_AUTH_ENABLED=false` / `MIP_RATE_LIMIT_ENABLED=false` by
   default).** MIP is offline-first, zero-config, single-user by default (Constitution Law 7); a
   fresh `MIPSettings()` must keep working exactly as before for local/dev use and for all 321
   pre-existing tests, none of which were touched. Multi-tenant/shared/production deployments opt in
   via environment variables — this is the intended "hardening" lever, not a new default posture.

3. **Auth is a FastAPI dependency (`require_principal`), not middleware.** Applied per-router via
   `dependencies=[Depends(require_principal)]` in `app.py`, except `GET /v1/health` and `GET
   /v1/version` (left public — orchestrator health probes and version negotiation must not require
   credentials) and `POST /v1/admin/rebuild-projections` (gated individually, same dependency, since
   it is destructive/expensive but lives in a router shared with the two public routes). A dependency
   (vs. middleware) keeps the check colocated with routing and gives route handlers typed access to
   the resolved `Principal` via `request.state.principal`.

4. **Namespace/ownership enforcement reuses the `namespace` field already on every Memory Object** —
   no new schema field. Three enforcement shapes, applied at their natural point: (a) writes that
   declare a namespace (`CreateMemory`) validate it directly; (b) reads that accept an optional
   namespace filter (`ListMemories`, `Search`, `BuildContext`, `Export`) validate it if given, or
   auto-scope to the key's single allowed namespace, or reject as ambiguous if the key has several and
   none was named (`resolve_scoped_namespace`); (c) per-memory operations (Get/Update/Delete/Archive/
   Restore/Consolidate/Learn/Explain/relationships) look up the target's namespace first and check it
   against the principal before delegating to the existing engine call — implemented via a new
   `MemoryManager.peek_namespace()` (raw record lookup, bypassing the Active/Deleted lifecycle gate)
   so the namespace check never disturbs Delete/Archive/Restore's existing idempotent-on-tombstone
   behavior (`_require_live_record` would incorrectly reject an already-Deleted memory with `MEM-2003`
   before the idempotency check ever ran).

5. **Import enforces namespace per-entry, not for the whole bundle.** `ImportEngine.import_bundle`
   gains an additive `allowed_namespaces: tuple[str, ...] | None = None` parameter; a version whose
   `identity.namespace` isn't permitted is added to the existing `rejected` list (same shape as a
   schema-validation failure) rather than failing the entire request — consistent with decision 9 of
   ADR-0006 (per-memory atomic, whole-bundle partial). `allowed_namespaces=None` (the default) means
   "unrestricted," so every existing caller/test is unaffected.

6. **Rate limiting is in-memory, per-process, keyed by API key (or client IP if unauthenticated).**
   A sliding 60-second window (`RateLimitMiddleware`) rejects with `MEM-8005` + `Retry-After` once a
   key/IP exceeds `MIP_RATE_LIMIT_REQUESTS_PER_MINUTE`. In-memory state is a deliberate simplification:
   MIP's storage model (SQLite, single-writer) does not assume horizontal scaling, so a single-process
   in-memory counter matches the existing deployment shape. A distributed store (Redis) would only be
   needed if MIP is ever run with multiple worker processes/instances behind a shared limit — that is
   out of scope here and documented as a known limitation, not built speculatively.

7. **Middleware order: `CORS(if configured) → RequestContext → RateLimit → router`.** Starlette wraps
   outermost-last-added; `RequestContextMiddleware` must run before `RateLimitMiddleware` so a 429
   response still carries a resolved `request_id`; CORS (only added when `MIP_CORS_ALLOWED_ORIGINS` is
   set) must be outermost so it decorates every response, including auth/rate-limit rejections.

8. **Deployment packaging targets single-process, single-worker uvicorn behind a container**, matching
   SQLite's single-writer model — `backend/Dockerfile` + root `docker-compose.yml` + `22-deployment.md`
   document this explicitly (`--workers 1`) rather than silently under-supporting multi-worker rate
   limiting/idempotency-store correctness. Scaling beyond one process is future work requiring its own
   ADR (Postgres-backed storage adapter + distributed rate limiter).

## Alternatives Considered

| Option | Why not chosen |
| --- | --- |
| Full identity/auth (accounts, sessions, RBAC) | Explicitly out of scope per `08-roadmap.md`; would require a roadmap/architecture rewrite and its own ADR — user chose the lightweight option instead. |
| Auth/rate-limit enabled by default | Breaks the zero-config, offline-first, single-user default (Constitution Law 7) and would have required touching all 321 pre-existing tests for a feature most local deployments don't need. |
| Auth as global middleware | A dependency scoped per-router is simpler to keep `/health`/`/version` public without a path-exclusion list inside the middleware itself. |
| Namespace check via `manager.get_memory()` for Delete/Archive/Restore pre-checks | Would raise `MEM-2003` for an already-Deleted memory before delete's own idempotency logic runs, breaking existing idempotent-delete tests; `peek_namespace()` (raw record, no lifecycle gate) avoids this. |
| Whole-bundle-reject on any namespace violation in Import | Inconsistent with ADR-0006's per-memory-atomic/whole-bundle-partial model; per-entry rejection reuses the existing `rejected` list shape instead of introducing a new failure mode. |
| Redis-backed distributed rate limiting | Speculative complexity for a single-process, SQLite-backed deployment; add only if/when MIP is horizontally scaled (Simplicity Wins). |

## Consequences

* Positive: zero behavior change for the default (auth/rate-limit disabled) configuration — all 321
  pre-existing backend tests pass unmodified; namespace isolation is enforced consistently across
  every write/read path that touches a specific memory or namespace; Import's namespace check follows
  the same partial-failure shape callers already handle.
* Negative / accepted trade-offs: rate limiting is not distributed (single-process only); API keys are
  static config, not rotatable via an API (rotation = redeploy with a new `MIP_API_KEYS` value); no
  admin-only key tier — any valid key can call `rebuild-projections` (acceptable for the lightweight
  tier chosen; network-level restriction of admin routes is a deployment-time concern, documented in
  `22-deployment.md`).
* Follow-ups: if MIP ever needs real user accounts/RBAC or horizontal scaling, both require their own
  ADR and an explicit roadmap change (this ADR does not authorize either).

## Compliance Notes

Does not alter the identity/auth-out-of-scope boundary in `08-roadmap.md` — API keys are an
authentication *mechanism* for the ownership/namespace isolation MIP already claimed
(`03-system-architecture.md`), not an identity system. No Phase 1-4 endpoint's request/response shape
changed. All new settings are additive with safe (disabled) defaults, preserving Constitution Law 7
(offline-first, zero-config by default).
