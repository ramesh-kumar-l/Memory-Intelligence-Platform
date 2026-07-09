# 30-Day Execution Plan

Assumes 3 hours/day. Sequenced so each week's output is a prerequisite for the next — no parallel workstreams that could stall independently.

## Week 1 — Ship the public-facing surface

- Replace the one-line root `README.md` with the drafted OSS README (`04-opensource-readme.md`), reviewed and verified against the actual current API/SDK behavior.
- Build the demo pack's first scenario for real (Create → Retrieve → Explain loop) as a runnable script in an `examples/` directory — the single highest-leverage proof that the explainability claim is real, not just documented.
- Close the one-line memory-bank open question (who edits the lifecycle-state enum in `30-memory/02-memory-schema.md`) — cheap, and it's been open five sessions.

## Week 2 — Prove the architecture claims

- Fill in the Benchmark Report's currently-placeholder sections with real numbers: retrieval latency and event-replay time on a synthetic dataset (hundreds to low-thousands of memories is enough for a first pass — don't over-invest here yet).
- Write and publish Blog Post #1 ("Your AI Doesn't Have Memory") — pure problem-framing, no pitch, to start building an audience before asking anyone to look at code.
- Decide the "next initiative" question from `26-active-initiatives.md` (Sync Engine vs. console UX vs. auth-tier extension) — this has been sitting open and blocks confidently answering "what's next" in any external conversation.

## Week 3 — Distribution

- Publish Blog Post #4 ("The Architecture Conflict I Stopped to Ask About") and the matching LinkedIn post — highest career-leverage content in the whole set, per the Career Leverage Analysis.
- Reach out to 1-2 developers building agentic AI products (warm network first) for early feedback on the SDK/CLI — the goal is a single real usage data point, not a launch.
- Draft the Talk Deck's speaker notes in full (not just the outline) so it's submission-ready for a local meetup CFP.

## Week 4 — Consolidate and decide

- Incorporate any Week 3 feedback into the README/demo pack (expect at least one rough edge in the SDK onboarding path — treat it as signal, not noise).
- Submit the talk to one concrete local meetup/CFP.
- Write the Staff Engineer Case Study and resume bullets into your actual resume/LinkedIn profile now, while the ADR-0007 story is fresh, rather than reconstructing it later from memory.
- End-of-month checkpoint: reassess the Startup Leverage Analysis's "PMF signals to watch for" against whatever actually happened in Weeks 3-4, and decide whether Month 2 leans further into OSS distribution, a reference application, or the next platform initiative.
