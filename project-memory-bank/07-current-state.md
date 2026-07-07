# 07-current-state.md

**Read at every session boot.** Keep under ~80 lines. Reflects reality — update before ending any session. (This file is the project's "implementation status" doc.)

**Last updated:** 2026-07-07

---

## Status: Phase 1 — Core Memory Engine COMPLETE (all gates green)

| Area | State |
| --- | --- |
| Specifications | ✅ Complete (`30-memory/01–06`); schema-state-enum drift resolved by ADR-0003 (state machine's 11 states authoritative) |
| Engineering OS | ✅ `CLAUDE.md` v2.0 + Constitution; operational docs 03/05/08/09/18/20/21 |
| Decisions | ✅ ADR-0001 Python/FastAPI/SQLite · ADR-0002 React/TS/Vite · ADR-0003 lifecycle enum + tombstone deletion |
| Backend Phase 1 | ✅ `backend/` — core domain (11-section frozen MemoryObject, MEM-* error registry), 11-state machine (13 legal transitions), SQLite event store + projections, Memory Manager + Validation engines, REST API `/v1` |
| Tests / gates | ✅ 208 tests green; ruff + mypy --strict clean; coverage 98% (core 99.7%, engines 96.4%) |
| Phase 2 (search/explain) | ❌ Not started (awaiting approval) |
| Frontend / SDKs / CLI | ❌ Not started (Phase 3) |
| Graph / learn / export | ❌ Not started (Phase 4) |

## What works right now

`uvicorn mip.api.main:app` serves: CreateMemory (full pipeline Created→…→Active, one event per hop), Get (+`?version=N`, `/versions`), Update (If-Match, version N+1), Delete (idempotent, tombstone), Archive/Restore (idempotent), list (continuation tokens), `/v1/health`, `/v1/version`, `/v1/admin/rebuild-projections` (replay ⇒ `identical: true`). Idempotency-Key replay, MIP-API-Version negotiation, structured MEM-1xxx…6xxx envelopes.

## Key implementation facts (for future sessions)

* Event → projection writes go through `mip/events/projector.py::apply_event` **only** — live path and rebuild share it, so replay is identical by construction.
* All SQL lives under `mip/storage/sqlite/`; engines see only ABCs in `storage/interfaces.py`.
* Deterministic tests: injected `Clock`; per-memory `LockRegistry` enforces INV-CONCUR-004.
* Only `Active → Deleted` is legal; deleting an Archived memory requires restore first (ADR-0003). GET on deleted → 410 `MEM-2003`.
* Quality gate (run from `backend/`, venv `.venv`): `ruff check . ; ruff format --check . ; mypy ; pytest`.

## Last completed milestone

Phase 1 — Core Memory Engine, 2026-07-07 (all acceptance criteria in `09-phase-plan.md` verified).

## Next milestone

Phase 2 — Retrieval & Explainability. **Blocked on: user approval to begin.**

## Known issues / open questions

* `30-memory/02-memory-schema.md` still lists the old 7-state enum; needs the additive spec edit recorded in ADR-0003 (user-owned normative doc).
* Nothing committed to git yet this phase (commit on request).
