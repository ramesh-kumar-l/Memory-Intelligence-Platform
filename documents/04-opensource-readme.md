# MIP — Memory Intelligence Platform

> A local-first Memory Operating System for AI-native systems: persistent, explainable, event-sourced memory behind a stable REST API — not another vector-store wrapper.

*(This is a drafted candidate for the repo's public-facing `README.md`, which currently contains only a title. Review before replacing.)*

## Positioning

Every agentic AI product hand-rolls memory today: a conversation buffer plus a vector index, with no lifecycle, no explainability, and no answer to "why did you retrieve that, and how confident should I be?" MIP is infrastructure that answers those questions natively, offline-first, with zero required cloud dependency.

## Features

- **Event-sourced Memory Objects** — every state change is an immutable, replayable event; current state is always a deterministic projection.
- **Explainability as an API, not a debug log** — `/v1/explain` returns evidence, provenance, and confidence for any memory.
- **Hybrid retrieval** — keyword (FTS5) + semantic (sqlite-vec) search with fused ranking, plus graph and temporal retrieval.
- **Trust metadata** — provenance, confidence, and freshness tracked on every memory, maturing through use (Consolidate/Learn).
- **Knowledge graph** — relationships between memories, queryable alongside content search.
- **Storage & model independence** — SQLite/local-embeddings by default, swappable behind explicit repository/provider interfaces — no code outside `storage/` touches SQL directly.
- **Opt-in production hardening** — API-key auth with namespace/ownership isolation, rate limiting, and Docker packaging, all disabled by default so local/zero-config use is untouched (ADR-0007).
- **Four client surfaces, one contract** — Python SDK, TypeScript SDK, CLI, and a React developer console, all against the same versioned REST API.

## Quick Start

```bash
# Backend (zero-config, SQLite, no auth required by default)
cd backend
pip install -e .
uvicorn mip.api.app:app --reload

# Python SDK
pip install mip-sdk
```

```python
from mip_sdk import MIPClient

client = MIPClient("http://localhost:8000")
memory = client.create_memory(content="...", namespace="personal")
results = client.search("what did I decide about X?", namespace="personal")
explanation = client.explain(memory.id)  # evidence, provenance, confidence
```

```bash
# CLI
pip install mip-cli
mip memories create --content "..." --namespace personal
mip search "what did I decide about X?"
```

```bash
# Deployment (opt-in auth + rate limiting)
docker compose up --build
# set MIP_AUTH_ENABLED=true and MIP_API_KEYS='{"key1":["namespace1"]}' to require keys
```

## Examples

See [`08-demo-examples-pack.md`](08-demo-examples-pack.md) for full runnable scenarios (personal memory assistant, engineering-session memory bank — this project's own `CLAUDE.md`/memory-bank pattern is itself a worked example, gallery/media memory).

## Roadmap

Phases 1-4 (Core Memory Engine, Retrieval & Explainability, Developer Platform, Intelligence) plus a Production Hardening pass (ADR-0007) are complete. Next candidates: Synchronization Engine (multi-device), console UX polish, extended auth tiers. See [`10-future-roadmap.md`](10-future-roadmap.md) and the project's own `project-memory-bank/08-roadmap.md`.

## Status

MVP — core platform, SDKs, CLI, console, and hardening are implemented and tested (342 backend tests / 97.6% coverage; full SDK/CLI/console test suites green), but the project has no external users or deployments yet. Treat as pre-1.0.
