# 29-session-handoff.md

**Read at every session boot.** Overwritten at the end of every session; keep under ~80 lines.

**Session date:** 2026-07-07 (session 2)

---

## What this session did

Implemented **Phase 1 — Core Memory Engine** end to end in `backend/` (user approved the phase; per-task stop-gates waived by explicit instruction to complete the phase):

1. Scaffold: `pyproject.toml` (ruff, mypy --strict, pytest+coverage), venv, README, .gitignore.
2. Core domain (`mip/core/`): frozen pydantic MemoryObject with all 11 schema sections; MEM-* error registry (`errors.py`, append-only); `CreateMemorySpec`/`UpdateMemorySpec`; INV-* activation checks; injectable Clock.
3. State machine (`core/states.py`): 11 states, exactly 13 legal transitions, `assert_legal` → MEM-2001.
4. Event sourcing (`mip/events/`): 14 event types (transition↔event bijection); `projector.apply_event` is the single write path for live ops **and** rebuild.
5. Storage (`mip/storage/`): ABCs + SQLite adapters (WAL, explicit transactions, nested-scope join); no SQL outside `storage/sqlite/`.
6. Engines: ValidationEngine; MemoryManager (create pipeline, If-Match update→v N+1, idempotent archive/restore/delete, per-memory LockRegistry, rebuild).
7. API (`mip/api/`): all Phase 1 endpoints, success/error envelopes, Idempotency-Key replay, MIP-API-Version negotiation, request/trace ids, lifespan DB close.
8. Tests (208): invariant suites (ID/STATE/VER/CONCUR + activation branches), full 13-legal + 108-illegal matrix, replay identity, API contract, idempotency.

## Decisions made

* **ADR-0003** (accepted): state machine's 11 states authoritative; tombstone deletion; only `Active→Deleted` legal (archived must be restored first); prose "ValidationFailed allows Delete" not implemented — table wins.
* Python 3.14 in use locally (satisfies `>=3.12`).
* Unexpected-500s map to `MEM-6002` (Storage category) — revisit if a Runtime category is ever added to the contract.

## Next steps

1. User reviews Phase 1 (run gates: `backend/` → `ruff check . ; mypy ; pytest`).
2. Optionally commit (`git add backend project-memory-bank CLAUDE.md ...` — nothing committed yet).
3. On approval: **Phase 2 task 1** (FTS5 keyword search + pagination). Load `03`, `05`, `30-memory/05-memory-api-contract.md`, `20`.

## Open questions (need user input)

1. Approve Phase 2 start?
2. Who edits `30-memory/02-memory-schema.md` state enum (additive, per ADR-0003)? Recommend user applies it since 30-memory specs are normative user-owned docs.

## Watch out for

* Keep every source file < 300 lines (user rule, session 2). Largest is `engines/memory_manager/engine.py` (~250) — split before extending.
* `uvicorn mip.api.main:app` (module-level app lives in `main.py`, not `app.py`, to avoid import-time DB creation).
* Windows: background shells may lack `python` on PATH — use `py` or the venv's `python.exe`.
