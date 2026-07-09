# Staff Engineer Case Study

*(Framed for Staff Engineer interview loops and promotion packets — emphasizes cross-cutting technical judgment and influence over an architecture, not individual PRs.)*

## Problem

Add production-hardening (auth, rate limiting, deployment packaging) to a memory platform whose own product requirements explicitly listed "identity/auth and billing" as **out of scope**, owned by a future, unbuilt subsystem (the "Semantic Control Plane"). Ship it across five packages (backend, two SDKs, CLI, console) without breaking any of 321 existing tests or changing default behavior for the platform's zero-config, offline-first users.

## Constraints

- A written architectural boundary (`08-roadmap.md`'s "Out of Scope") directly conflicted with the literal ask ("add auth").
- Zero tolerance for regressions: every new setting had to default to off/empty so existing tests and deployments were provably unaffected.
- A hard, self-imposed 300-line-per-file modularity rule, enforced retroactively, not just on new files.
- Idempotency guarantees already relied upon elsewhere in the system (Delete/Archive/Restore on already-deleted memories) could not be silently broken by adding an ownership check in front of them.

## Architecture

Resolved the roadmap conflict by stopping and asking before writing code — the literal request ("add auth") and the literal architecture ("identity/auth is out of scope") could not both be followed without a decision only the product owner could make. Framed the fork as a scoped choice (lightweight API-key + namespace isolation vs. full identity system) rather than silently picking one, producing ADR-0007 as the record. Implemented the chosen scope as: a static API-key → namespace map (config, not a user/accounts table); auth as a FastAPI *dependency* (composable per-router) instead of global middleware, so `/health`/`/version` stay public without special-casing; three namespace-enforcement shapes (direct validation on writes, auto-scoping for list/search reads, post-fetch checks for per-memory operations) reusing the *existing* `namespace` field rather than adding new schema surface.

## Tradeoffs

Chose a **static config map over a database-backed key system** — sufficient for the stated scope (ownership isolation, not multi-tenant SaaS), and avoids building session/rotation/revocation machinery the roadmap doesn't yet call for. Chose **in-memory single-process rate limiting over Redis** — consistent with the platform's existing single-writer SQLite model; building distributed rate limiting for a system that doesn't yet run more than one process would be speculative. Chose **per-entry import rejection over whole-bundle failure** for namespace violations — deliberately reused a pattern an earlier ADR (0006) had already established for a different failure class, keeping the system's failure semantics consistent rather than inventing a new one.

## Impact

Delivered auth + namespace isolation + rate limiting + Docker packaging across all 5 packages with **zero regressions** (342 backend / 42 SDK / 24 CLI / 40+ TS-SDK / 52 frontend tests, all green) and **zero required config changes** for any existing deployment. Caught and fixed three real bugs before they shipped by re-running full quality gates after each change rather than only at the end: a case where an SDK's `api_key` argument would have silently been dropped whenever a caller also supplied their own HTTP client; a case where a namespace check would have broken an existing idempotent-delete guarantee; and a file that quietly grew past the team's own file-size budget.

## Lessons Learned

The highest-leverage moment in the whole pass was the five minutes spent noticing a conflict *before* writing code, not the code itself — reversing that order (implement first, discover the roadmap conflict during review) would have produced either a silent architecture violation or wasted implementation work. Enforcing "every new setting defaults to off" as a hard rule, rather than a best-effort intention, is what made "zero regressions across 5 packages" a checkable claim instead of an assumption. A self-imposed constraint (300-line file budget) is only real if it's enforced retroactively — the moment a file crosses the line during unrelated work is exactly when it's tempting to let it slide.
