# Reusable Asset Catalog

Patterns from this project worth extracting and reusing on *other* projects — the actual "Learning Impact" payoff of this whole exercise. Each entry names where it lives in this repo so it can be lifted directly.

## Process / Operating-Model Patterns

- **Single-system-prompt operating model** (`CLAUDE.md`) — a project-root file that is *the* entrypoint for an AI collaborator, with an explicit "Session Boot Protocol" (read exactly N short files, nothing else) and a "Task → File Routing Table" mapping task type to the specific docs needed. Portable to any AI-assisted project regardless of domain.
- **Memory bank / compressed save-state pattern** (`project-memory-bank/07-current-state.md`, `26-active-initiatives.md`, `29-session-handoff.md`) — three short, aggressively size-budgeted (~80 lines) living docs that get rewritten at the end of every session, versus one sprawling changelog. The size budget is the important part — it's what keeps the "read at every boot" cost cheap indefinitely.
- **ADR-required-on-conflict rule** — "if implementation conflicts with documented architecture: stop, explain, wait for approval" as a *standing instruction*, not a one-off judgment call. This is what turned the auth-scope conflict in this session into a deliberate decision (ADR-0007) instead of a silent one.
- **Phase-gate protocol** (`CLAUDE.md`'s Implementation Workflow + Phase-Gate Protocol) — plan → pause for approval → implement incrementally → test → update docs → stop-and-summarize, with an explicit "never auto-continue to the next phase" rule. Reusable on any multi-phase project where uncontrolled scope creep is the main risk.

## Engineering Patterns

- **ADR template** (`project-memory-bank/adr/ADR-template.md`) — Context / Decision / Alternatives / Consequences skeleton, reused identically across all 7 ADRs in this project.
- **Invariant-ID-to-test mapping** (`20-testing-strategy.md`, `30-memory/04-memory-invariants.md`) — every named invariant (`INV-*`) maps to at least one always-green test; makes "is this invariant actually enforced" a checkable fact instead of a design-doc claim.
- **Event-sourcing-with-regenerable-projections** — Memory Objects as source of truth, indexes/graph/vectors as replayable projections, `rebuild_projections` as a first-class recovery operation. Directly portable to any domain-object system where derived read models (search indexes, caches, denormalized views) need a trustworthy "rebuild from scratch" story.
- **Storage/provider independence via explicit ABCs** (`storage/interfaces.py`, `EmbeddingProviderABC`) enforced by a stated rule ("no code outside `storage/` may import sqlite3") — the rule is only real because it's named explicitly and checkable by grep, not left as an implicit convention.
- **Self-imposed file-size budget, enforced retroactively** — the 300-line rule and the `errors.py` split it triggered this session is a concrete, low-cost discipline that keeps an AI collaborator (or any new contributor) able to read one file instead of a 1000-line module to answer a question.
- **Dependency-not-middleware auth pattern** (`api/middleware/auth.py::require_principal`) — applying auth as a per-router FastAPI dependency rather than blanket middleware, so public routes (health/version) are excluded by omission rather than by exception-listing inside a middleware.

## Templates Worth Copy-Pasting Directly

- `project-memory-bank/adr/ADR-template.md`
- The three session-state docs' headers ("Read at every session boot," "Keep under ~80 lines," "Overwritten at the end of every session")
- The Task → File Routing Table format in `CLAUDE.md` (task type ↔ doc path)
- This artifact set's own Pareto-scoring table format (`00-INDEX.md`) — reusable for prioritizing *any* backlog, not just career artifacts.
