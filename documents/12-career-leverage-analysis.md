# Career Leverage Analysis

Framed for the stated goal: **Staff Engineer.**

## FAANG / Staff Engineer Interviews

The system-design round is the direct target: MIP's architecture (hexagonal layout, event sourcing, storage independence, hybrid retrieval) is a complete, defensible answer to "design a memory/context system for an AI product" — and unlike a whiteboard design, every claim is backed by a working, tested implementation you can cite line-by-line. The "tell me about a time you caught a design conflict" behavioral question has a real, specific answer in the ADR-0007 story (roadmap said auth was out of scope; stopped and asked rather than guessing) — use the Staff Engineer Case Study (`06-staff-engineer-case-study.md`) almost verbatim as prep notes.

## Principal Engineer Interviews (if the ladder extends there later)

The gap between this project's evidence and Principal-level signal is scope of *organizational* influence — this project demonstrates technical judgment on a single system, not cross-team architectural authority. If pursuing Principal later, the artifact to build is evidence of the pattern (ADR discipline, phase-gating, conflict-surfacing) being adopted by *other* engineers or teams, not just self-applied.

## Resume

Bullet candidates (verify numbers against the repo before using externally):
- "Designed and shipped an event-sourced memory platform (Python/FastAPI/SQLite) with a hexagonal architecture, hybrid retrieval, and an explainability API, maintaining 97%+ test coverage across 342 backend tests."
- "Identified a conflict between a production-hardening request and documented product scope before implementation; resolved it via a written architecture decision record rather than an ad-hoc judgment call, then shipped auth/rate-limiting/deployment packaging across 5 packages with zero regressions."
- "Enforced a self-imposed code-modularity budget (300 lines/file) across a multi-package system, including retroactive refactors, keeping the codebase navigable for both human and AI-assisted contributors."

## LinkedIn

A single post reusing Blog post #4 ("The Architecture Conflict I Stopped to Ask About") performs better than a project-announcement post — it demonstrates judgment, not just output, and is the kind of story that gets saved/shared by other engineers, not just liked.

## Conference Talks

The Talk Deck (`09-talk-presentation-deck.md`) is CFP-ready for infra/backend-adjacent local meetups today; hold off on larger conference CFPs until either a live demo audience reaction has been tested at a smaller venue, or a reference application exists to make the demo concrete rather than architectural.

## Technical Leadership Signal

The clearest technical-leadership artifact isn't a single decision — it's the *operating system* itself (`CLAUDE.md` + memory bank + ADR discipline + phase gating). Very few individual contributors build the process scaffolding for how decisions get made and recorded, not just the decisions themselves; this is squarely Staff-level signal and should be named explicitly in interviews rather than left implicit in the code.
