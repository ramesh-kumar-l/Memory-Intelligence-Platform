# 29-session-handoff.md

**Read at every session boot.** Overwritten at the end of every session; keep under ~80 lines.

**Session date:** 2026-07-09 (session 6)

---

## What this session did

Implemented **Production Hardening** (auth, rate limiting, deployment packaging) after the user
asked to "continue with a production-hardening pass." Flagged a real conflict before starting:
`08-roadmap.md` lists identity/auth as out of scope for MIP (owned by a future Semantic Control
Plane) — asked the user how to resolve it; they chose the lightweight option ("API-key auth +
namespace/ownership enforcement, no accounts"), which became ADR-0007.

1. **Auth**: `api/middleware/auth.py` — `Principal`, `require_principal` (FastAPI dependency, not
   middleware), `ensure_namespace_allowed`, `resolve_scoped_namespace`. Opt-in via
   `MIP_AUTH_ENABLED` + `MIP_API_KEYS` (JSON key→namespaces map, `["*"]` = unrestricted). Applied
   per-router in `app.py` to every `/v1` route except `/v1/health`/`/v1/version`; admin's
   `rebuild-projections` gated individually.
2. **Namespace/ownership enforcement**: reuses the existing `namespace` field — writes validate
   it, list/search-style reads auto-scope or reject ambiguity (`MEM-8004`), per-memory ops
   (Get/Update/Delete/Archive/Restore/Consolidate/Learn/Explain/relationships) check the target's
   namespace first. New `MemoryManager.peek_namespace()` (raw lookup, bypasses the lifecycle gate)
   was required so Delete/Archive/Restore's idempotent-on-tombstone behavior wasn't broken by the
   namespace check. Import rejects (not fails) out-of-scope entries per-memory.
3. **Rate limiting**: `api/middleware/rate_limit.py` — in-memory sliding 60s window, opt-in via
   `MIP_RATE_LIMIT_ENABLED`, keyed by API key or client IP, `MEM-8005` + `Retry-After`.
4. **Deployment packaging**: `backend/Dockerfile` (single uvicorn worker — matches SQLite's
   single-writer model), root `docker-compose.yml`, new `project-memory-bank/22-deployment.md`.
5. **`mip/core/errors.py` split into a package** (`errors/base.py` + `errors/factories.py`,
   re-exported from `errors/__init__.py`) — adding the 5 new `MEM-8xxx` codes pushed it to 317
   lines, over the 300-line budget; the split is a zero-behavior-change mechanical refactor (every
   `from mip.core import errors` call site keeps working identically).
6. All 4 client surfaces updated: Python SDK (`api_key` param, sent as `Authorization: Bearer`),
   TypeScript SDK (same), CLI (`--api-key` / `MIP_API_KEY`), console (Settings page API-key field,
   stored in localStorage like the base URL).
7. Full quality gate rerun on all 5 packages after every meaningful change; caught and fixed two
   real bugs along the way (see below) rather than only at the end.

## Decisions made

* **ADR-0007** (accepted) — auth is a static API-key→namespaces map, not an identity system;
  auth/rate-limit default OFF (zero-config, offline-first stays the default); auth is a dependency
  not middleware; single-process rate limiting (no Redis) since MIP doesn't assume horizontal
  scaling; Import rejects per-entry, not whole-bundle, for namespace violations.
* Did **not** change `08-roadmap.md`'s identity/auth-out-of-scope line — added a note that ADR-0007
  authenticates ownership/namespace isolation MIP already claimed, not a new identity system.

## Bugs found and fixed mid-session

* A lambda default-arg pattern (`lambda mid=target_id: ...`) broke mypy's generic inference in
  `consolidate.py`; switched to `asyncio.to_thread(manager.peek_namespace, target_id)` directly.
* First cut of the namespace pre-check for Delete/Archive/Restore used `manager.get_memory()`,
  which raises `MEM-2003` for an already-Deleted memory — would have broken existing
  idempotent-delete tests. Fixed by adding `peek_namespace()` (raw record, no lifecycle gate).

## Next steps

1. User reviews this pass (same gate commands as before, per package).
2. Optionally commit (nothing committed yet).
3. Discuss what comes next — Sync Engine, console UX polish, or extending the auth tier — see
   `26-active-initiatives.md`'s "Next up".

## Open questions (need user input)

1. What comes after this — Sync Engine, console UX polish, or something else?
2. Who edits `30-memory/02-memory-schema.md` state enum (still open from Phase 1/ADR-0003)?

## Watch out for

* Keep every source file < 300 lines — `mip/core/errors.py` crossed it this session and was split
  into a package; check again before adding more factories/routes to any file near the limit.
* Auth/rate-limit are OFF by default — don't assume a fresh `MIPSettings()` requires a key; only
  the dedicated `test_auth.py`/`test_rate_limit.py` fixtures enable them.
* `docker-compose.yml` and `backend/Dockerfile` are new and untested against a real container
  runtime in this session (no Docker available in the harness) — verify `docker compose up --build`
  actually works before relying on it for a real deployment.
