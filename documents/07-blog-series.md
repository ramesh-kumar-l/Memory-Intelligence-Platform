# Blog Series

10 posts, ordered for compounding distribution: each early post seeds the audience for the next. Titles are working titles.

## Publishing Order

1. **"Your AI Doesn't Have Memory — It Has a Vector Store With Amnesia"**
   The problem-framing post. Why conversation-buffer-plus-embeddings isn't memory: no lifecycle, no explainability, no trust model. Sets up MIP's whole thesis without pitching the project yet.

2. **"Why I Modeled Memory as Events, Not Rows"**
   Deep dive on event sourcing for Memory Objects: immutable log, deterministic projections, `rebuild_projections` as a first-class recovery mechanism. Technical, code-forward.

3. **"Explainability Isn't a Debug Log — It's an API"**
   Walks through `/v1/explain`: evidence, provenance, confidence as a contract, not an afterthought. Include a real request/response example.

4. **"The Architecture Conflict I Stopped to Ask About"**
   Narrative post built directly from the ADR-0007 story: a written spec said "auth is out of scope," a stakeholder asked for auth anyway, and the right move was to pause and resolve the conflict explicitly rather than pick a side silently. Strong career-signal post; doubles as a case study teaser.

5. **"Storage Independence Is a Discipline, Not a Feature"**
   How the repository-abstraction rule (`no code outside storage/ may import sqlite3`) is enforced, why it matters, and what it cost vs. what it bought.

6. **"Building Two SDKs and a CLI Off One Contract Without Drifting"**
   Developer-platform post: OpenAPI as the shared source of truth, the CLI-on-top-of-the-SDK decision (ADR-0005), and the known follow-up (regenerating TS types from OpenAPI instead of hand-writing them).

7. **"What I Learned Enforcing a 300-Line File Budget on Myself"**
   Practical, widely relatable engineering-practice post. Real example: `errors.py` crossing the limit and getting split into a package with zero import-path changes.

8. **"Adding Auth to a System That Said It Didn't Need It"**
   Technical companion to post 4 — the actual implementation: dependency vs. middleware, the three namespace-enforcement shapes, `peek_namespace()` and why idempotent deletes forced its existence.

9. **"Trust Metadata: Making 'How Confident Should I Be?' a First-Class Question"**
   Product-and-architecture crossover post on the Trust Engine, confidence/provenance/freshness, and how trust matures through Consolidate/Learn.

10. **"Six Months, Seven ADRs: What a Written Decision Trail Actually Buys You"**
    Retrospective/meta post — distribution bait for engineering-culture audiences, not just AI-infra audiences. Reuses the ADR Collection almost directly.
