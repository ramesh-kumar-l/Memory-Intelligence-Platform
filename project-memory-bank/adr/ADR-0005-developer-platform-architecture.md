# ADR-0005: Developer Platform Architecture — SDKs, CLI, Console

**Status:** Accepted
**Date:** 2026-07-08
**Deciders:** Project owner (user), Phase 3 session

## Context

Phase 3's objective (`09-phase-plan.md`) is that any engineer can use MIP in minutes: a console, a CLI, and typed SDKs in Python and TypeScript. All of these are clients of the public REST API only (`03-system-architecture.md` — "Frontend & Clients"); none may embed engine/storage logic. Several concrete decisions were needed before writing code: how SDKs stay in sync with the API contract without hand-duplication (`21-coding-standards.md`), what HTTP/CLI/UI libraries to add, and how the new top-level packages relate to each other and to `backend/`.

## Decision

**Layout** — three new top-level packages, each independently installable/buildable, none importing backend internals:

```text
sdk/python/        mip_sdk       — thin typed client over REST (httpx)
sdk/typescript/     @mip/sdk      — thin typed client over REST (fetch)
cli/                mip-cli       — Click CLI built on mip_sdk
frontend/           console       — React + TS + Vite, built on @mip/sdk
```

`frontend/` and `sdk/typescript/` are linked via npm workspaces (root `package.json`) so the console imports `@mip/sdk` locally without publishing — no type duplication between them.

**Type generation** — `backend/scripts/export_openapi.py` dumps `app.openapi()` (FastAPI-generated, doc not contract per `05-api-design.md`) to `sdk/typescript/openapi.json`. `sdk/typescript` runs `openapi-typescript` (dev dependency) over that file to produce `src/generated/schema.ts`. **Discovered during implementation:** the backend's routes return raw `JSONResponse` envelopes rather than `response_model=`-typed bodies (deliberate — the envelope/error-translation logic in `api/responses.py` is shared, hand-written, and not itself a Pydantic model), so FastAPI's OpenAPI output has empty (`{}`) response schemas throughout; `openapi-typescript` can only generate anything useful for **request** bodies (`CreateMemoryRequest`, `UpdateMemoryRequest`, `SearchRequest`, etc. — genuinely generated, imported by `src/types.ts`, never redeclared). Response types (`MemoryObject`, `SearchResponse`, `Explanation`, `ContextPackage`, ...) are hand-written in `src/types.ts`, mirrored field-for-field from `sdk/python/mip_sdk/models/{memory,retrieval}.py` — the same accepted asymmetry as the Python SDK below, now proven to be forced by the backend's actual response typing rather than a convenience choice. Revisit only if routes adopt `response_model=` (would itself need an ADR, since it changes response serialization behavior). The Python SDK has no codegen step: pydantic v2 models are hand-written directly against the DTOs in `backend/mip/api/v1/schemas.py` / `retrieval_schemas.py`, kept in sync manually because pydantic-to-pydantic codegen from OpenAPI adds more risk than it removes for a same-language, same-repo pair.

**HTTP clients** — Python SDK uses `httpx` (already a transitive dependency of the backend's own test suite, sync API, connection pooling, well-typed). TypeScript SDK uses the platform `fetch` (Node ≥18 / all evergreen browsers) — zero runtime dependency.

**CLI** — built with `click` (new dependency, justified: the standard, boring choice for multi-command Python CLIs with argument parsing, help text, and exit codes for free — avoids hand-rolling `argparse` subparser boilerplate). Every command is a thin wrapper: parse args → call `mip_sdk` → format output (table or `--json`). No business logic in the CLI layer.

**Error mapping** — both SDKs mirror the `MEM-*` envelope (`05-api-design.md`) as a typed exception hierarchy parallel to `backend/mip/core/errors.py`'s categories (Validation/Lifecycle/Identity/Concurrency/Trust/Storage/Sync/Security), keyed on `error.code`, never on message text — so client code can catch `LifecycleError` / a specific `MEM-2001` the same way server code does.

**Console** — React 18 + TypeScript strict + Vite, TanStack Query for server state (no global store), React Router for the four-pane layout in `18-ui-design-system.md` (Memories · Search · Events · Settings — Graph is Phase 4 and omitted), CSS custom properties for the design-token theme (light/dark via `prefers-color-scheme` + manual override), no UI kit — components are bespoke per the design system, consistent with ADR-0002.

## Alternatives Considered

| Option | Why not chosen |
| --- | --- |
| Generate the Python SDK from OpenAPI too (e.g. `datamodel-code-generator`) | Extra codegen dependency and build step for marginal benefit within the same language/repo; hand-written pydantic models are already type-checked against the same backend by mypy in CI-equivalent gates |
| `argparse` for the CLI (zero new dependency) | Subcommand groups, auto-generated help, and shell-completion hooks are exactly `click`'s job; avoiding one boring, widely-used dependency was not worth the boilerplate |
| Publish `@mip/sdk` to a registry and have the console depend on a version | Adds release-process overhead before the SDK has any external consumer; npm workspaces give the same import ergonomics locally with zero publishing surface |
| Redux/Zustand for console state | Server state is 95% of console state and TanStack Query owns it; no cross-cutting client state exists yet (Simplicity Wins, per `21-coding-standards.md`) |

## Consequences

* Positive: SDKs and console cannot silently drift from the REST contract (TS types generated; Python types exercised against the same error/DTO modules via tests); CLI adds zero new engine surface area; console can be deleted/rebuilt without touching `backend/`.
* Negative / accepted trade-offs: two independent type sources (generated TS vs hand-written Python) require discipline on future API changes — any DTO change must be reflected in both `sdk/python/mip_sdk/models.py` and by re-running the TS export script; this is a manual step, not yet CI-enforced.
* Follow-ups: if a CI pipeline is introduced later, add a check that `sdk/typescript/openapi.json` is not stale relative to `backend/mip/api/**`. Not built now (no CI exists yet — Simplicity Wins).

## Compliance Notes

All four new packages are optional tooling on top of the public API (FR-API-001 preserved); none read SQLite directly or import `mip.core`/`mip.engines`/`mip.storage`. Explainability is surfaced as a first-class UI concern (ExplainPanel renders `/v1/explain` directly) per the Constitution's explainability law.
