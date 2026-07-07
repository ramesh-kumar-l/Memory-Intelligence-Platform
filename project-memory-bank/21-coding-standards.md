# 21-coding-standards.md

**Read this when:** writing or reviewing any code.

**TL;DR:** Python 3.12 + FastAPI + pydantic v2, ruff + mypy strict, typed everything, structured errors from a single `MIPError` hierarchy, no SQL outside `storage/`. TypeScript strict for frontend/SDK. Small reviewable changes; extend, never rewrite.

---

## Python (backend, Python SDK, CLI)

* **Version/tooling:** Python 3.12+. `ruff` (lint + format), `mypy --strict`, pytest. Config in `pyproject.toml`; CI enforces all three.
* **Types:** full annotations everywhere, including tests. No `Any` in public signatures; no `# type: ignore` without a reason comment.
* **Models:** pydantic v2 for all domain models and DTOs. Domain models in `mip/core` are frozen (`model_config = ConfigDict(frozen=True)`) — immutability by construction; updates build new instances/versions.
* **Naming:** `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE` constants. Modules are nouns (`states.py`), functions verb phrases (`apply_transition`). Names mirror spec vocabulary exactly (`memory_id`, `GraphLinked`, `CreateMemory`) — never invent synonyms.
* **Errors:** single hierarchy in `mip/core/errors.py`: `MIPError(code, category, message, details, recoverable)` with subclasses per category (ValidationError→`MEM-1xxx`, LifecycleError→`MEM-2xxx`, IdentityError→`MEM-3xxx`, ConcurrencyError→`MEM-4xxx`, TrustError→`MEM-5xxx`, StorageError→`MEM-6xxx`, SyncError→`MEM-7xxx`, SecurityError→`MEM-8xxx`). Never `raise Exception`; never bare `except:`; never swallow exceptions — translate at layer boundaries, preserve `__cause__` via `raise … from …`. The API layer is the only place errors become HTTP responses.
* **Logging:** stdlib `logging` with structured `extra` (always include `request_id`/`trace_id`/`memory_id` when available). No `print`. Never log memory content, payloads, or anything potentially sensitive — log identifiers and outcomes.
* **Docstrings:** Google style on all public modules/classes/functions — one-line summary plus the *why* and contract (raises, invariants touched). No docstrings that restate the signature.
* **Layering:** `core` imports nothing from api/engines/storage/events. Engines depend on interfaces (ABCs), wired via FastAPI dependency injection. `sqlite3`/SQL strings appear only under `mip/storage/sqlite/`. No global mutable state.
* **Async:** API and engine entry points `async def`; SQLite access via a thread-executor wrapper behind the repository interface. Never block the event loop.
* **Dependencies:** minimal and boring. Adding a runtime dependency requires justification in the PR description; anything architectural requires an ADR.

## TypeScript (frontend, TS SDK)

* `strict: true` (all strict flags), ESLint + Prettier, no `any` (use `unknown` + narrowing). React function components + hooks; state via TanStack Query for server state, local state otherwise — no global store until proven necessary. API types generated from OpenAPI (`openapi-typescript`) — never hand-duplicated. SDK errors mirror the `MEM-*` envelope as typed classes.

## Both

* **Change discipline:** extend, don't replace (Constitution Law: Stability Before Refactoring). No drive-by refactors, no reformatting unrelated files, no large-scale renames without approval.
* **Comments:** explain *why* and constraints, not *what*. Spec references (`INV-CONCUR-001`, `FR-API-005`) welcome where code enforces them.
* **Commits:** Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`) with scope, e.g. `feat(lifecycle): reject illegal transitions with MEM-2004`. One logical change per commit; tests and docs in the same commit as the behavior they cover.
* **PRs/summaries:** state objectives, files changed, tests run, risks — per the Completion Protocol in `CLAUDE.md`.
