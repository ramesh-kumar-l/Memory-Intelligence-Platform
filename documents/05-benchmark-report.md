# Benchmark Report

**Status note:** MIP has no external users and no dedicated performance-benchmarking harness yet — the numbers below are *quality/engineering-rigor* metrics that exist today (test suites, coverage), not throughput/latency benchmarks. This report is templated so it can be filled in accurately as soon as a load-testing pass exists; it deliberately does not fabricate latency numbers.

## Metrics (available today)

| Package | Tests | Coverage | Lint/Type gates |
| --- | --- | --- | --- |
| Backend (`backend/`) | 342 | 97.6% (floor: 85%) | ruff, ruff format, mypy --strict — all clean |
| Python SDK (`sdk/python/`) | 42 | 99.3% | ruff, mypy --strict — clean |
| CLI (`cli/`) | 24 | 93.4% | ruff, mypy --strict — clean |
| TypeScript SDK (`sdk/typescript/`) | 40 mock + live-server suite | n/a (TS) | eslint, tsc — clean |
| Frontend console (`frontend/`) | 52 | n/a (TS) | eslint, tsc, production build — clean |

## Methodology (for the metrics above)

Each package's quality gate is defined in its own tooling config and re-run after every meaningful change within a session (not just at merge time) — this is a stated engineering practice (`CLAUDE.md`/`21-coding-standards.md`), not a one-off CI check. Coverage floors are enforced (backend: 85% minimum, currently 97.6%). Invariant tests (`INV-*` IDs from `30-memory/04-memory-invariants.md`) and state-machine transition tests are maintained as an "always-green" suite per `20-testing-strategy.md`.

## Baselines

No external baseline exists yet (no comparable benchmark run against Mem0, Zep, or a raw vector-store + LLM pipeline). This is the single highest-value addition to this report once the project has bandwidth: a same-corpus, same-queries comparison of retrieval precision/recall and explainability completeness against 1-2 comparable OSS memory libraries.

## Results

Not yet measured: query latency (P50/P95/P99) under concurrent load, retrieval precision/recall on a labeled dataset, memory-consolidation accuracy, event-replay (`rebuild_projections`) time as event-log size grows. These are exactly the four success metrics named in `00-PRD-Overview.md` ("Product Quality" and "Reliability" sections) and should be the first four numbers produced once real usage exists.

## Conclusions

The project's engineering-rigor metrics (test count, coverage, zero-lint-error gates across 5 packages) are genuinely strong and are honest, verifiable signals today. Performance/quality-of-retrieval benchmarks are the correct next investment *after* real usage patterns exist to benchmark against — building a synthetic benchmark now, with no real workload to validate it against, would itself be premature complexity (Simplicity Wins). Recommendation: defer a full benchmark report until either (a) a reference application is dogfooding MIP, or (b) an external user provides a representative workload.
