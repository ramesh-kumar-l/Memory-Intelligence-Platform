# 08-roadmap.md

**Read this when:** you need the big picture of where the platform is going. For executable detail, use `09-phase-plan.md`.

**TL;DR:** Five PRD milestones delivered through four implementation phases. Core = Phases 1–2 (memory engine + retrieval/explainability). Platform = Phase 3 (SDKs, CLI, console). Intelligence = Phase 4 (graph, learning, trust maturity).

---

## Milestones (from `00-PRD-Overview.md`)

| Milestone | Outcome | Delivered by |
| --- | --- | --- |
| M1 — Architecture Foundation | Specs, architecture, ADRs, engineering OS in place | Foundation session (done 2026-07) + Phase 1 scaffold |
| M2 — Core Memory Engine | Memory Objects with full lifecycle, event sourcing, CRUD API, retrieval + explainability | Phases 1–2 |
| M3 — Developer Platform | Python/TS SDKs, CLI, developer console | Phase 3 |
| M4 — Reference Applications | Gallery Assistant, Engineering Memory Demo | after Phase 4 |
| M5 — Production Readiness | Hardening, performance, packaging, docs site | after Phase 4 |

## Implementation Phases (capability roadmap from `01-product-requirements.md`)

| Phase | Name | Capabilities | Status |
| - | --- | --- | --- |
| 1 | Core Memory Engine | Memory Object model, schema validation, state machine, event store, CRUD/Archive/Restore API | Awaiting approval |
| 2 | Retrieval & Explainability | Keyword/semantic/hybrid search, Explain, BuildContext, basic Trust metadata | Not started |
| 3 | Developer Platform | React console, CLI, Python SDK, TypeScript SDK | Not started |
| 4 | Intelligence | Knowledge graph, Learning, Consolidate, Import/Export, trust maturation | Not started |
| — | Production Hardening | API-key auth + namespace isolation (opt-in), rate limiting, Docker packaging | Done (ADR-0007) |
| — | Future | Synchronization, Android/Kotlin SDK + IPC, MCP transport, gRPC, ecosystem/plugins, enterprise | Backlog |

## Out of Scope (per PRD)

Model training, workflow automation, cloud orchestration, identity/auth and billing, governance/privacy policy (owned by the Semantic Control Plane). This boundary is unchanged by ADR-0007's opt-in API-key mechanism, which authenticates the ownership/namespace isolation MIP already claims — it is not an accounts/sessions/RBAC system.

## Rules

Phases execute strictly in order, each gated by explicit user approval (`CLAUDE.md` Phase-Gate Protocol). Scope changes to this roadmap require user approval; architecture-affecting changes also require an ADR.
