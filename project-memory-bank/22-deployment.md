# 22-deployment.md

**Read this when:** packaging, deploying, or hardening the backend for shared/production use
(auth, rate limiting, CORS, containers). See `ADR-0007` for the design rationale.

**TL;DR:** MIP ships zero-config and offline-first by default (auth/rate-limit disabled, no
CORS). A single Docker image runs one uvicorn worker (matches SQLite's single-writer model).
Hardening is opt-in via `MIP_*` environment variables — never required for local/single-user use.

---

## Running locally (no container)

```bash
cd backend
pip install -e .
uvicorn mip.api.main:app --reload
```

## Running with Docker

```bash
docker compose up --build
```

Builds `backend/Dockerfile`, serves on `http://localhost:8000`, persists SQLite data in the
`mip-data` named volume. `--workers 1` is intentional — do not scale workers without also
moving to a distributed store for the rate limiter and a networked database (out of scope; see
ADR-0007 follow-ups).

## Production hardening (opt-in)

All disabled by default. Enable per deployment via environment variables (`docker-compose.yml`
`environment:` block, or your orchestrator's secret/config mechanism):

| Variable | Default | Purpose |
| --- | --- | --- |
| `MIP_AUTH_ENABLED` | `false` | Require an API key on every `/v1` route except `/v1/health` and `/v1/version`. |
| `MIP_API_KEYS` | `{}` | JSON map of `{"<key>": ["<namespace>", ...]}`. Use `["*"]` for an unrestricted key. Send the key as `Authorization: Bearer <key>` or `X-API-Key: <key>`. |
| `MIP_RATE_LIMIT_ENABLED` | `false` | Enable the in-memory sliding-window rate limiter. |
| `MIP_RATE_LIMIT_REQUESTS_PER_MINUTE` | `120` | Per-key (or per-IP if unauthenticated) request ceiling; exceeding it returns `MEM-8005` + `Retry-After`. |
| `MIP_CORS_ALLOWED_ORIGINS` | `[]` | JSON list of allowed browser origins for the console/other SPA clients. Empty disables CORS middleware entirely. |

Example production override:

```bash
export MIP_AUTH_ENABLED=true
export MIP_API_KEYS='{"console-prod": ["team-a"], "ops-admin": ["*"]}'
export MIP_RATE_LIMIT_ENABLED=true
export MIP_RATE_LIMIT_REQUESTS_PER_MINUTE=300
export MIP_CORS_ALLOWED_ORIGINS='["https://console.example.com"]'
```

## Known limitations (accepted, see ADR-0007)

* **Rate limiting is single-process.** Running multiple backend instances/workers behind a load
  balancer gives each its own counter — the effective limit multiplies. Fine for the default
  single-instance deployment; needs a Redis-backed limiter (its own ADR) before scaling out.
* **No admin-only key tier.** Any valid API key can call `POST /v1/admin/rebuild-projections`.
  Restrict this route at the network/reverse-proxy layer if stricter isolation is required.
  Full RBAC is out of MIP's scope (`08-roadmap.md`) — API keys are ownership/namespace scoping,
  not an identity system.
* **API keys are static config**, not rotatable via an API — rotate by redeploying with a new
  `MIP_API_KEYS` value.

## Health & readiness

`GET /v1/health` checks storage connectivity (used by the Docker `HEALTHCHECK` and should be
wired to your orchestrator's liveness/readiness probe). It never requires an API key.
