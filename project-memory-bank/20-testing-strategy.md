# 20-testing-strategy.md

**Read this when:** writing any test, or checking whether a feature meets Definition of Done.

**TL;DR:** pytest pyramid over `backend/tests/` mirroring `mip/`. Three always-green normative suites — invariants, state machine, API contract — plus per-engine unit tests. Every bug fix ships with a regression test. No feature is complete without validation.

---

## Pyramid

| Level | Scope | Tooling | Speed |
| --- | --- | --- | --- |
| Unit | `core/` (pure domain) + each engine in isolation | pytest, no I/O, fakes for interfaces | ms |
| Integration | engines + real SQLite adapters (tmp db per test) | pytest + fixtures | fast |
| API contract | full FastAPI app via `TestClient` | pytest + httpx | fast |
| E2E / UI (Phase 3+) | console against a live backend | Vitest (components) + Playwright (flows) | slow, CI-gated |

## Normative Suites (never allowed to be red or skipped)

1. **Invariant suite** — `tests/invariants/`. Every applicable `INV-*` ID from `30-memory/04-memory-invariants.md` maps to at least one test named after it (e.g. `test_inv_state_003_deleted_is_terminal`). Groups: ID, STATE, VER, SEM, REL, TRUST, CONS, CONCUR, INT, API, REC now; SYNC when sync lands. Traceability = grep the invariant ID.
2. **State machine suite** — `tests/lifecycle/`. Parametrized over the full legal-transition table of `30-memory/03-memory-state-machine.md` (all 13 legal transitions succeed + emit the right event) and the full illegal matrix (every other from→to pair rejected with `MEM-2xxx`). Plus replay test: rebuild from events ⇒ identical projection.
3. **API contract suite** — `tests/api/`. Per endpoint: success shape (`request_id`, `schema_version` present), error envelope shape, idempotency behavior (repeated DELETE succeeds; repeated `Idempotency-Key` returns original result), `If-Match` conflict → `MEM-4xxx`, pagination via continuation token, version negotiation.

## Rules

* **Determinism:** no sleeps, no wall-clock coupling (inject clock), no network, no shared state between tests. Seed anything random.
* **Regression policy:** every bug fix includes a test that fails on the pre-fix code, named/commented with the issue reference.
* **Coverage:** `mip/core` ≥ 95%, engines ≥ 90%, overall ≥ 85% (enforced in CI). Coverage is a floor, not a goal — the normative suites matter more.
* **Fixtures:** canonical valid Memory Object factory in `tests/factories.py`; invalid-object cases enumerate each required field violation from `30-memory/02-memory-schema.md`.
* **Property-based tests** (hypothesis) encouraged for version monotonicity, transition ordering, and serialization round-trips.
* Frontend (Phase 3): component tests for every design-system component's states (default/hover/focus/disabled/empty/error, light+dark); Playwright smoke: create → find → explain → archive → restore.

## CI Gates

`ruff check` + `ruff format --check` + `mypy --strict` + full pytest + coverage floors. A red normative suite blocks merge, always.
