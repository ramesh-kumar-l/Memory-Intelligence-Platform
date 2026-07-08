# 05-api-design.md

**Read this when:** adding/changing any REST endpoint, DTO, error, header, or versioning behavior.

**TL;DR:** REST binding of the transport-independent contract in `30-memory/05-memory-api-contract.md`. The contract defines semantics; this doc defines the HTTP surface. Semantics may never be altered by transport (FR-API-001).

---

## Conventions

* Base path `/v1`. JSON request/response bodies, `snake_case` fields, UTC ISO-8601 timestamps, UUIDs as strings.
* Every response includes `request_id`, `schema_version`, `processing_time_ms`.
* Headers: `MIP-API-Version` (version negotiation; unknown versions → structured negotiation error), `Idempotency-Key` (required semantics for Create/Update/Learn retries), `X-Request-Id` / `X-Trace-Id` (generated if absent), `Authorization: Bearer <api-key>` or `X-API-Key` (only enforced when `MIP_AUTH_ENABLED=true`; ADR-0007 — see `22-deployment.md`).
* OpenAPI is generated from code (FastAPI) and published; it is documentation, not the contract.

## Auth & Namespace Isolation (opt-in, ADR-0007)

Disabled by default (zero-config, offline-first). When `MIP_AUTH_ENABLED=true`, every `/v1` route
except `GET /v1/health` and `GET /v1/version` requires a recognized API key (`MIP_API_KEYS`, a
JSON map of key → allowed namespaces; `["*"]` = unrestricted). This is authentication for the
ownership/namespace isolation MIP already claims (`03-system-architecture.md`) — not an identity
system; full auth/RBAC remains out of scope per `08-roadmap.md`. Enforcement:
* Writes that declare a namespace (`CreateMemory`) validate it directly.
* Reads with an optional namespace filter (`ListMemories`, `Search`, `BuildContext`, `Export`)
  validate it if given, auto-scope to a key's single allowed namespace if omitted, or reject as
  ambiguous (`MEM-8004`) if the key has several and none was named.
* Per-memory operations (Get/Update/Delete/Archive/Restore/Consolidate/Learn/Explain/
  relationships) check the target's namespace against the key before delegating to the engine.
* Import rejects (not fails the whole bundle) any entry whose namespace isn't permitted.

Rate limiting (`MIP_RATE_LIMIT_ENABLED`, also opt-in) is a single-process, per-key/IP sliding
60-second window; exceeding it returns `MEM-8005` + `Retry-After`.

## Endpoints ↔ Canonical Operations

| Operation | Method & Path | Phase | Notes |
| --- | --- | - | --- |
| CreateMemory | `POST /v1/memories` | 1 | 201; starts lifecycle; emits `MemoryCreated` |
| GetMemory | `GET /v1/memories/{memory_id}` | 1 | latest active version; `?version=N` for history |
| UpdateMemory | `PATCH /v1/memories/{memory_id}` | 1 | creates version N+1, never overwrites; requires `If-Match: <version>` (optimistic concurrency) |
| DeleteMemory | `DELETE /v1/memories/{memory_id}` | 1 | idempotent — repeated delete returns success (FR-API-005) |
| Archive | `POST /v1/memories/{memory_id}/archive` | 1 | idempotent |
| Restore | `POST /v1/memories/{memory_id}/restore` | 1 | idempotent |
| Search | `POST /v1/search` | 2/4 | body: `query`, `mode` (keyword/semantic/hybrid/graph), filters, `continuation_token`. Mode `graph` (Phase 4, ADR-0006) treats `query` as the seed `memory_id`; score = `1/hop_distance`. `timeline`/`relationship`/`context` modes from the contract are not yet implemented — unsupported modes return `MEM-1007`. |
| BuildContext | `POST /v1/context` | 2 | returns Context Package |
| Explain | `POST /v1/explain` | 2 | evidence, confidence, freshness, provenance, ranking explanation — available for every retrieval (FR-API-007) |
| — relationships | `GET /v1/memories/{memory_id}/relationships` | 4 | read-only graph-projection view: every edge touching this memory, outbound and inbound (ADR-0006, additive) |
| Consolidate | `POST /v1/consolidate` | 4 | body: `primary_memory_id`, `duplicate_memory_ids[]`. Merges duplicates via a `duplicate_of` relationship + archive; history preserved, nothing deleted |
| Learn | `POST /v1/learn` | 4 | body: `memory_id`, `derived` (Semantics, unioned non-destructively), `new_evidence[]`/`verifier` (trust maturation — appended, never replaces evidence), `reason`. Supports `Idempotency-Key` like Create/Update |
| Export | `POST /v1/export` | 4 | body: `namespace?`. Backup/migration; excludes Deleted tombstones by default |
| Import | `POST /v1/import` | 4 | body: an Export bundle. Validates every version of every memory before writing; per-memory atomic, whole-bundle partial (`imported`/`skipped`/`rejected`) |
| — health | `GET /v1/health` | 1 | liveness + storage check |
| — version | `GET /v1/version` | 1 | accepted/supported API versions, upgrade guidance |

List endpoint `GET /v1/memories?namespace=…&state=…&continuation_token=…` (Phase 1) is a filtered read, not Search.

## Error Envelope

All failures return:

```json
{
  "error": {
    "code": "MEM-2004",
    "category": "Lifecycle",
    "message": "Illegal lifecycle transition",
    "details": {"from": "Deleted", "to": "Active"},
    "recoverable": false,
    "documentation_url": "https://…/errors#MEM-2004"
  },
  "request_id": "…"
}
```

Code namespaces (from the contract): `MEM-1000` Validation · `MEM-2000` Lifecycle · `MEM-3000` Identity · `MEM-4000` Concurrency · `MEM-5000` Trust · `MEM-6000` Storage · `MEM-7000` Sync · `MEM-8000` Security (`MEM-8001` missing API key · `MEM-8002` invalid API key · `MEM-8003` namespace forbidden · `MEM-8004` namespace required · `MEM-8005` rate limit exceeded — ADR-0007). HTTP status is a coarse mapping (400/404/409/422/500…); clients must key on `code`, never on message text. The code registry lives in `backend/mip/core/errors/` (split into `base.py`/`factories.py` for the 300-line file budget; both re-exported from `errors/__init__.py`) and is append-only.

## Pagination & Partial Results

Continuation-token based only — offset pagination is prohibited by the contract. Search responses include `complete: bool`, `continuation_token`, and `warnings[]` when partial.

## Idempotency

Idempotent by definition: GetMemory, Search, Explain, Archive, Restore, DeleteMemory. CreateMemory/UpdateMemory/Learn become idempotent when the client sends `Idempotency-Key`; a repeated key returns the original result (keys stored with response hash, bounded TTL).

## Versioning & Deprecation

* Minor versions: additive fields only; clients must tolerate unknown fields.
* Major versions: new base path (`/v2`), migration guide + deprecation window + ADR required.
* Deprecated endpoints keep working during the window and return a `Deprecation` header with replacement guidance. Silent removal prohibited.

## Non-negotiables

* Every retrieval is explainable. Every operation emits an audit event (FR-API-008). No endpoint exposes storage identifiers (Section 9 of the schema) or lets clients touch SQL/graph/vector internals. Breaking changes require an ADR and user approval.
