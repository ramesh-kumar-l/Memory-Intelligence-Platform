# MIP Leverage Artifact Set — Index

**Inputs used:** Career Goal = Staff Engineer · Primary Objective = Mixed (OSS + Career + Startup) · Stage = MVP (Phases 1-4 + Production Hardening complete, no external users yet) · Generated 2026-07-09.

This folder contains the highest-leverage artifact set derivable from the Memory Intelligence Platform (MIP) codebase and memory bank as it stands today. Everything here is a **derivative work product** — none of it changes `project-memory-bank/` (the engineering source of truth) or any source code.

---

## Step 1 — Project Analysis

**Core innovation:** MIP treats memory as a first-class, event-sourced domain object — not a vector-DB wrapper. Every Memory Object carries lifecycle state, provenance, confidence, and an explainability contract (`/v1/explain` returns evidence + reasoning, not just a score). Retrieval, graph, and vector indexes are regenerable projections of an immutable event log, never the source of truth.

**Technical complexity:** Hexagonal (ports & adapters) backend in Python/FastAPI over SQLite (WAL + FTS5 + sqlite-vec), a documented state machine with legal-transition enforcement, per-memory advisory-lock concurrency, invariant-driven testing (`INV-*` IDs map 1:1 to test cases), two typed SDKs generated/maintained against one OpenAPI contract, and an opt-in auth/rate-limit/deployment layer added without touching any of 321 pre-existing tests.

**Differentiators:** explainability as a first-class API (not a debug log), trust/confidence metadata on every memory, offline-first/local-first by default (zero-config SQLite, no cloud dependency), storage- and model-provider independence via explicit interfaces, and a strict engineering operating system (`CLAUDE.md` + `ENGINEERING_CONSTITUTION.md`) that enforces ADRs for every architecture-affecting decision — producing a paper trail (7 ADRs) that doubles as a design-rationale archive.

**Market relevance:** Every agentic-AI product currently hand-rolls memory (conversation history + a vector store) with no lifecycle, no explainability, and no trust model. MIP is a credible answer to "what does memory infrastructure look like once agentic AI matures past demos" — a thesis several funded startups and OSS projects (Mem0, Zep, Letta/MemGPT) are independently converging on.

**Career signal value:** The repo demonstrates staff-level judgment, not just code output — conflict detection against a written spec (the ADR-0007 auth-scope stop-and-ask), phase-gated delivery with acceptance criteria, and a self-imposed 300-line file budget enforced retroactively. These are the artifacts staff-level interview loops (system design + "tell me about a technical decision") are built to probe.

**Startup potential:** Real, but unproven — MVP stage, zero external users. The honest leverage today is technical credibility and distribution groundwork, not revenue.

**Open source potential:** High. The combination of (a) a working, tested reference implementation and (b) a fully public engineering-decision trail (ADRs + memory bank) is rare in OSS infra projects and is itself a distribution asset.

---

## Step 2 — Artifact Universe

| Category | Candidate artifacts |
| --- | --- |
| Architecture | System architecture doc, sequence diagrams, storage abstraction doc, engine map |
| Engineering | ADR collection, benchmark report, testing strategy writeup, coding standards writeup |
| Product | PRD-derived positioning doc, roadmap, use-case gallery |
| Research | Memory-lifecycle-as-event-sourcing thesis, explainability-in-retrieval writeup |
| Career | Staff engineer case study, resume bullets, LinkedIn narrative, interview talking points |
| Content | Blog series, talk deck, demo pack, README |
| Open Source | README, CONTRIBUTING, roadmap, issue-shaped "good first issue" list |
| Enterprise | Deployment/hardening doc (already exists: `22-deployment.md`), security posture summary |
| Community | Talk deck, blog series, demo pack |
| Learning | Reusable asset catalog (ADR template, memory-bank pattern, invariant-test pattern) |

~25 raw candidates. Step 3 scores them; Step 4 keeps only the top 10 plus the 4 analysis deliverables mandated by the template (reusable assets, career leverage, startup leverage, 30-day plan).

---

## Step 3 — Pareto Scoring

Scale 1–10 per dimension; **Leverage Score = (Career + OSS + Startup + Learning + Distribution) / Effort**, so a good score means high combined impact for low effort.

| Artifact | Career | OSS | Startup | Learning | Distribution | Effort | Leverage |
| --- | - | - | - | - | - | - | - |
| Engineering Thesis | 9 | 8 | 7 | 6 | 8 | 3 | **12.7** |
| Architecture Document | 9 | 7 | 5 | 8 | 5 | 4 | **8.5** |
| ADR Collection | 9 | 6 | 4 | 9 | 4 | 2 | **16.0** |
| OSS README | 6 | 10 | 8 | 4 | 10 | 3 | **12.7** |
| Benchmark Report | 6 | 6 | 6 | 5 | 5 | 6 | **4.7** |
| Staff Eng. Case Study | 10 | 3 | 4 | 6 | 4 | 3 | **9.0** |
| Blog Series (outlines) | 8 | 7 | 6 | 5 | 9 | 4 | **8.75** |
| Demo & Examples Pack | 5 | 8 | 6 | 4 | 7 | 5 | **6.0** |
| Talk / Presentation Deck | 8 | 5 | 5 | 4 | 8 | 4 | **7.5** |
| Future Roadmap | 5 | 6 | 6 | 3 | 4 | 2 | **12.0** |
| Reusable Asset Catalog | 6 | 5 | 3 | 10 | 3 | 2 | **13.5** |
| Career Leverage Analysis | 10 | 1 | 2 | 5 | 2 | 1 | **20.0** |
| Startup Leverage Analysis | 3 | 2 | 10 | 3 | 2 | 1 | **20.0** |
| 30-Day Execution Plan | 6 | 3 | 5 | 4 | 2 | 1 | **20.0** |

**Not selected (below the line, revisit only if stage advances):** dedicated CONTRIBUTING.md (premature pre-first-external-contributor), Playwright/E2E showcase video, conference CFP submissions (needs the talk deck first), governance/RFC process doc (premature at MVP with a single maintainer).

---

## Step 4 — The 80/20 Set (final selection, 10 artifacts + 4 analyses)

| # | Artifact | Primary audience | Priority |
| - | --- | --- | --- |
| 1 | [Engineering Thesis](01-engineering-thesis.md) | Hiring panels, OSS visitors, future collaborators | P0 |
| 2 | [Architecture Document](02-architecture-document.md) | Engineers evaluating/adopting MIP, interview panels | P0 |
| 3 | [ADR Collection](03-adr-collection.md) | Contributors, staff-level interviewers | P0 |
| 4 | [Open Source README](04-opensource-readme.md) | GitHub visitors, first adopters | P0 |
| 5 | [Benchmark Report](05-benchmark-report.md) | Technical evaluators, blog readers | P1 |
| 6 | [Staff Engineer Case Study](06-staff-engineer-case-study.md) | Interview panels, promo/leveling committees | P0 |
| 7 | [Blog Series](07-blog-series.md) | Developer audience, distribution | P1 |
| 8 | [Demo & Examples Pack](08-demo-examples-pack.md) | New adopters, README readers | P1 |
| 9 | [Talk / Presentation Deck](09-talk-presentation-deck.md) | Conference/meetup audiences | P2 |
| 10 | [Future Roadmap](10-future-roadmap.md) | Contributors, prospective users | P1 |
| — | [Reusable Asset Catalog](11-reusable-asset-catalog.md) | Future-you, other projects | P0 |
| — | [Career Leverage Analysis](12-career-leverage-analysis.md) | You (interview prep) | P0 |
| — | [Startup Leverage Analysis](13-startup-leverage-analysis.md) | You (optionality assessment) | P1 |
| — | [30-Day Execution Plan](14-30-day-execution-plan.md) | You (execution) | P0 |

**Cut for now:** benchmark automation infra, video demo, conference submission itself — all *derivative* of artifacts above; produce them only after #4 and #8 exist and get initial feedback.
