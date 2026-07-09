# Demo & Examples Pack

## Top Example Projects (buildable on top of MIP as-is)

1. **Personal Memory Assistant** — a CLI/chat wrapper that stores conversation-derived facts as Memory Objects in a `personal` namespace, retrieves via hybrid search before each response, and surfaces `/v1/explain` output inline ("I recall this because... confidence: 0.82"). Demonstrates the core retrieval + explainability loop end to end.
2. **Engineering Session Memory Bank** — this repository's *own* `CLAUDE.md` + `project-memory-bank/` pattern, reframed as a worked example: a coding agent that persists project state, decisions, and open questions between sessions via MIP instead of hand-maintained markdown files. (Meta-demo: MIP could eventually host what it currently simulates by convention.)
3. **Gallery/Media Memory** (named explicitly in the PRD's use cases) — ingest photo metadata + captions as experiences, use Consolidate to merge duplicate/near-duplicate memories, and Learn to raise trust on repeatedly-confirmed facts (e.g., recurring people/places).

## Demo Scenarios (for a live walkthrough or recorded demo)

- **Create → Retrieve → Explain loop**: create a memory, search for it semantically with a paraphrased query (not exact keyword match), then call `/v1/explain` on the result to show evidence and confidence — the single best "this isn't just a vector store" demo moment.
- **Namespace isolation under auth**: two API keys scoped to different namespaces, same content, showing that a key scoped to `namespace-a` cannot read or write `namespace-b` (`MEM-8003`) — good for a security-focused audience.
- **Idempotent delete on a tombstone**: delete a memory twice, show the second call succeeds identically rather than erroring — a small but concrete illustration of lifecycle-state discipline paying off.
- **Import with partial rejection**: import a bundle where one entry violates a namespace or invariant, show the other N-1 entries succeed and the violator is reported individually, not silently dropped or failing the whole batch.
- **Event replay**: mutate a memory a few times, then run `rebuild_projections` and show the resulting state is byte-identical to before — the event-sourcing payoff made visible.

## Customer Stories (aspirational — no real users yet; write only after first adopter feedback)

*Placeholder deliberately left unfilled.* Do not fabricate customer stories before MIP has real adopters — this would undermine the credibility that is the project's actual current asset. Revisit this section after the first external user (even a friendly early-access one) provides usable feedback.
