# Talk / Presentation Deck

## Talk Title

**"Memory Is Not a Vector Store: Building an Operating System for What AI Systems Know"**

## Audience

Local AI/ML meetups, backend/infra-focused engineering conferences (e.g., tracks adjacent to data infrastructure or agentic-AI content), and internal tech talks. Assumes working backend engineers, not a general/product audience — the deck goes into event sourcing and API contract design, not just product framing.

## Outline

1. **The problem** (2 min) — every AI app hand-rolls memory; show a minimal "conversation buffer + vector index" diagram and name what's missing: lifecycle, explainability, trust.
2. **The thesis** (2 min) — memory as infrastructure, not application code; the four questions from the Vision doc ("What do I know? Why? Can I trust it? How should it evolve?").
3. **Architecture walkthrough** (8 min) — hexagonal layout, event sourcing, the storage/model independence rule, live or recorded terminal demo of create → retrieve → explain.
4. **The hard part: explainability as an API** (5 min) — `/v1/explain` contract, a real response payload on screen, why this is different from a similarity score.
5. **A real conflict, told honestly** (4 min) — the ADR-0007 story: a written spec said auth was out of scope, the ask was "add auth anyway," and the resolution was a paused, explicit decision instead of silently picking a side. This is the credibility-building section — real engineering judgment, not just a feature tour.
6. **What's next / how to get involved** (3 min) — roadmap (Sync Engine, ecosystem), and a concrete ask (try the SDK, file issues, especially explainability/retrieval-quality feedback).
7. **Q&A**

## Key Slides

- Slide: the 3-layer AI stack diagram from `Vision.md` (Applications → Agent Runtime → **Memory Intelligence Platform** → Foundation Models → Compute) — the single most reusable slide for framing why this layer matters.
- Slide: hexagonal architecture diagram (from the Architecture Document) — dependency-rule arrows pointing one direction only.
- Slide: a real `/v1/explain` JSON response, annotated live.
- Slide: the ADR-0007 conflict, shown as two direct quotes side by side (roadmap's "out of scope" line vs. the ask) — makes the "stop and ask" story concrete instead of abstract.
- Closing slide: current status honestly stated — MVP, 5-package test suite all green, no external users yet, here's how to be the first.
