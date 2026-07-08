# 07-current-state.md

**Read at every session boot.** Keep under ~80 lines. Reflects reality — update before ending any session. (This file is the project's "implementation status" doc.)

**Last updated:** 2026-07-08

---

## Status: Phase 3 — Developer Platform COMPLETE (all gates green)

| Area | State |
| --- | --- |
| Specifications | ✅ Complete (`30-memory/01–06`); lifecycle enum drift resolved by ADR-0003 |
| Engineering OS | ✅ `CLAUDE.md` v2.0 + Constitution; operational docs 03/05/08/09/18/20/21 |
| Decisions | ✅ ADR-0001 Python/FastAPI/SQLite · ADR-0002 React/TS/Vite · ADR-0003 lifecycle/deletion · ADR-0004 retrieval/explainability · ADR-0005 developer platform (SDKs/CLI/console) |
| Backend Phase 1 | ✅ Core domain, 11-state machine, event store, Memory Manager, REST API `/v1` CRUD+lifecycle |
| Backend Phase 2 | ✅ FTS5/sqlite-vec retrieval, hybrid ranking, `/v1/search`, `/v1/explain`, `/v1/context`, enrichment, Trust scoring |
| Phase 3 — SDKs | ✅ `sdk/python` (mip_sdk, httpx), `sdk/typescript` (@mip/sdk, fetch, OpenAPI-generated request types) |
| Phase 3 — CLI | ✅ `cli` (mip_cli, Click, built on mip_sdk) — memories/search/explain/context/admin commands |
| Phase 3 — Console | ✅ `frontend` (React 18/TS/Vite) — Memories, Search, Settings pages; design-system components |
| Tests / gates | ✅ Backend 98.07% · sdk/python 30 tests · cli 16 tests · sdk/typescript 29 tests · frontend 45 tests — all ruff/mypy/eslint/tsc clean |
| Graph / learn / export | ❌ Not started (Phase 4) |

## What works right now

Everything from Phase 1/2, plus a full developer platform: **Python SDK** (`sdk/python`,
`pip install -e sdk/python`) and **TypeScript SDK** (`sdk/typescript`, `@mip/sdk`) both
wrap the full `/v1` surface (memories CRUD/lifecycle, search/explain/context, admin)
with typed `MEM-*` error hierarchies. **CLI** (`cli`, `mip` command) is a thin Click
wrapper over the Python SDK. **Console** (`frontend`, npm workspace linked to
`sdk/typescript`) has Memories (list + Overview/Semantics/Relationships/Trust/History
detail tabs), Search (per-result "Why this result?"), and Settings pages, following
`18-ui-design-system.md` (light/dark, keyboard nav, empty/error states). All three
runnable quickstart examples (`examples/{python,typescript,cli}`) were executed
against a live backend during this session, not just written.

## Key implementation facts (for future sessions)

* `sdk/python`/`cli`/`sdk/typescript`/`frontend` each have their own venv/`node_modules` and quality-gate config; none import backend internals — REST only (FR-API-001).
* `GET /v1/memories` (list) and `.../versions` return **lightweight projections** (`MemoryRecord`, `VersionInfo`), not full `MemoryObject` — a real shape mismatch was caught and fixed in both SDKs during this session (see ADR-0005 / session handoff).
* TS SDK: request types generated via `openapi-typescript` (`backend/scripts/export_openapi.py` → `sdk/typescript/openapi.json` → `npm run generate:types`); response types are hand-written in `src/types.ts` because backend routes return raw `JSONResponse`, not `response_model=`-typed bodies — OpenAPI has no response schema to generate from.
* Console has no Graph or global Events page — Graph is Phase 4; a per-memory History tab (version list) substitutes for a global event feed, which has no backing endpoint yet.
* Quality gates: backend `ruff/mypy/pytest`; sdk/python and cli same; sdk/typescript `eslint/tsc/vitest/tsc-build`; frontend same. All 5 run from their own directory with their own venv/node_modules.

## Last completed milestone

Phase 3 — Developer Platform, 2026-07-08 (all `09-phase-plan.md` acceptance criteria verified: console passes design-system checklist item-by-item, SDKs preserve contract semantics with typed errors, all three quickstarts run end-to-end on this machine).

## Next milestone

Phase 4 — Intelligence (knowledge graph, Consolidate, Learn, Export/Import, trust maturation). **Blocked on: user approval to begin.**

## Known issues / open questions

* `30-memory/02-memory-schema.md` still lists the old 7-state enum; needs the additive edit recorded in ADR-0003 (user-owned normative doc).
* Nothing committed to git this session either; commit on request.
