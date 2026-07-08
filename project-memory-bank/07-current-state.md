# 07-current-state.md

**Read at every session boot.** Keep under ~80 lines. Reflects reality — update before ending any session. (This file is the project's "implementation status" doc.)

**Last updated:** 2026-07-09

---

## Status: Phases 1-4 COMPLETE + Production Hardening COMPLETE (all gates green)

| Area | State |
| --- | --- |
| Specifications | ✅ Complete (`30-memory/01–06`); lifecycle enum drift resolved by ADR-0003 |
| Engineering OS | ✅ `CLAUDE.md` v2.0 + Constitution; operational docs 03/05/08/09/18/20/21/22 |
| Decisions | ✅ ADR-0001..0006 (stack, lifecycle, retrieval, dev platform, intelligence) · ADR-0007 production hardening |
| Phase 1-4 | ✅ Core, Retrieval/Explainability, Dev Platform, Intelligence — see ADRs 0003-0006 |
| Hardening — Auth | ✅ Opt-in API-key gate + namespace/ownership isolation (`MIP_AUTH_ENABLED`, `MIP_API_KEYS`), all `/v1` except `/health`/`/version` |
| Hardening — Rate limiting | ✅ Opt-in in-memory sliding-window limiter (`MIP_RATE_LIMIT_ENABLED`), `MEM-8005` + `Retry-After` |
| Hardening — Deployment | ✅ `backend/Dockerfile` + root `docker-compose.yml`, single-worker (matches SQLite single-writer model) |
| Tests / gates | ✅ Backend 97.6% (342 tests) · sdk/python 99.3% (42) · cli 93.4% (24) · sdk/typescript (42 incl. live) · frontend (52) — all ruff/mypy/eslint/tsc clean |

## What works right now

Everything from Phases 1-4, plus: opt-in API-key authentication enforcing ownership/namespace
isolation on every `/v1` route except health/version (`Authorization: Bearer <key>` or
`X-API-Key`); opt-in per-key/IP rate limiting; Docker packaging. All disabled by default — a
fresh `MIPSettings()` behaves exactly as before (zero-config, offline-first). All four client
surfaces (Python SDK, TS SDK, CLI `--api-key`/`MIP_API_KEY`, console Settings page) can supply an
API key when a deployment enables auth.

## Key implementation facts (for future sessions)

* Auth is a FastAPI dependency (`api/middleware/auth.py::require_principal`), not middleware —
  applied per-router in `app.py`; `/v1/health`/`/v1/version` stay public, `rebuild-projections` is
  gated individually since it shares admin's router with them.
* `MemoryManager.peek_namespace()` (new, additive) does a raw record lookup bypassing the
  Active/Deleted lifecycle gate — required so namespace checks on Delete/Archive/Restore don't
  break their existing idempotent-on-tombstone behavior (`get_memory` would 410 on a
  already-Deleted memory before idempotency logic runs).
* `ImportEngine.import_bundle` gained an additive `allowed_namespaces` param (default `None` =
  unrestricted); a disallowed entry is `rejected` like any other validation failure, not a
  whole-bundle failure.
* Rate limiting is single-process/in-memory by design — matches SQLite's single-writer model;
  do not run the Docker image with `--workers > 1` (documented limitation, see `22-deployment.md`).
* `mip/core/errors.py` was split into a package (`errors/base.py` + `errors/factories.py`,
  re-exported from `errors/__init__.py`) to stay under the 300-line file budget after adding the
  5 new `MEM-8001..8005` codes — zero change to any import path (`from mip.core import errors`
  still works identically).
* New error codes: `MEM-8001` missing API key · `MEM-8002` invalid API key · `MEM-8003` namespace
  forbidden · `MEM-8004` namespace required · `MEM-8005` rate limit exceeded.

## Last completed milestone

Production Hardening (ADR-0007), 2026-07-09: API-key auth + namespace isolation (opt-in), rate
limiting (opt-in), Docker packaging — full stack (backend, both SDKs, CLI, console) updated, all
gates green, zero behavior change when disabled (the default).

## Next milestone

`09-phase-plan.md`'s four phases plus hardening are now all complete. **Blocked on: user
direction** for what comes next (Synchronization Engine, console UX polish, or a new initiative).

## Known issues / open questions

* `30-memory/02-memory-schema.md` still lists the old 7-state enum; needs the additive edit
  recorded in ADR-0003 (user-owned normative doc, open since Phase 1).
* No admin-only API-key tier — any valid key can call `rebuild-projections` (accepted trade-off
  for the lightweight auth tier; see ADR-0007 known limitations).
* Nothing committed to git this session; commit on request.
