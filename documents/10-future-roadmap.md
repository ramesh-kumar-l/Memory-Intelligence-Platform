# Future Roadmap

Grounded in `project-memory-bank/26-active-initiatives.md`'s "Next up" and parking-lot items — this is a leverage-lens reprioritization of that same list, not a new plan. Any actual scope commitment still requires the phase-gate approval process defined in `CLAUDE.md`.

## Next 3 Months

- **Decide and scope the next initiative** — the memory bank currently lists three live candidates (Synchronization Engine, console UX polish, extending the auth tier) with no ranking; the highest-leverage first move is simply forcing that decision, since every artifact in this pack (README, demo pack, talk deck) benefits more from *a* clear direction than from any one specific direction.
- **Ship the OSS README and demo pack** (from this artifact set) as the real, public `README.md` and a `examples/` directory — currently the repo's actual README is a single line, which undersells a genuinely tested, working platform.
- **Close the one open cross-session question**: who applies the additive edit to `30-memory/02-memory-schema.md`'s lifecycle-state enum (open since Phase 1, per ADR-0003) — small, but it's been carried unresolved across five sessions and is cheap to close.

## Next 6 Months

- **First reference application** (per `00-PRD-Overview.md` Milestone 4: Gallery Assistant or Engineering Memory Demo) — the highest-leverage way to generate real benchmark data (Section 5 of this pack) and real customer-story material (Section 8), both currently placeholders for good reason (no usage yet to draw from).
- **Synchronization Engine**, if chosen as the next initiative — multi-device memory sync is explicitly named as "future" in the architecture doc and is the most product-differentiating item on the parking lot list.
- **Admin-only API-key tier** — currently any valid key can call `rebuild-projections`; a real deployment (even internal) will surface this as a genuine gap before six months are out.

## Next 12 Months

- **Milestone 5 (Production Readiness)** per the PRD: formal benchmarks (once real workloads exist to benchmark), observability, and a stable tagged release — natural point to also revisit whether SQLite's single-writer ceiling has become a real constraint (vs. hypothetical) and whether the storage abstraction needs its first alternate adapter.
- **Ecosystem groundwork** — plugin/connector points, if and only if an actual third-party integration need has appeared; per the project's own "Simplicity Wins" principle, this should follow real demand, not precede it.
- **Reassess identity/auth scope** — ADR-0007 deliberately deferred full identity/accounts to the future Semantic Control Plane; if a real multi-tenant or SaaS use case materializes, this is the point to revisit that boundary with a fresh ADR rather than extend the lightweight key system past its intended scope.
