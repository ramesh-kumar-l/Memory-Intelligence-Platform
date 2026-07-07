# 18-ui-design-system.md

**Read this when:** building or changing anything user-facing (developer console, docs UI).

**TL;DR:** The console is an instrument panel for trust: calm, dense-but-legible, explainability-first. Premium feel comes from restraint — one accent color, strict type/spacing scales, immaculate states (loading/empty/error), full keyboard support, flawless light/dark. If the `/frontend-design` skill is available, invoke it for UI work; this document remains the authoritative spec either way.

---

## Design Principles

1. **Trust through transparency.** Every screen answers: *What happened? Why? What can the user do next?* Confidence, provenance, and lifecycle state are always visible, never buried.
2. **Clarity over novelty.** No decorative animation, no gradients-for-gradients'-sake. Motion only to communicate state change (≤200ms, ease-out, respects `prefers-reduced-motion`).
3. **Information hierarchy.** One primary action per view. Metadata recedes (smaller, muted); knowledge content leads.
4. **Deterministic UI.** Same data → same pixels. No layout shift: skeletons match final layout; timestamps rendered stable (UTC with local tooltip).

## Design Tokens

**Type** — UI: system stack (`Inter, ui-sans-serif, system-ui`); data/IDs/code: `ui-monospace, 'JetBrains Mono', monospace`. Scale (px): 12 (meta) · 13 (body-sm) · 14 (body, default) · 16 (h3) · 20 (h2) · 24 (h1). Weights 400/500/600 only. Line height 1.5 body, 1.25 headings.

**Spacing** — 4px base scale: 4, 8, 12, 16, 24, 32, 48. Radius: 6 (controls), 10 (cards). Max content width 1200px; detail panes 720px.

**Color roles** (CSS variables, light / dark):

| Role | Light | Dark |
| --- | --- | --- |
| `--bg` | #FAFAF9 | #101113 |
| `--surface` | #FFFFFF | #1A1C1F |
| `--border` | #E7E5E4 | #2C2F33 |
| `--text` | #1C1917 | #ECEDEE |
| `--text-muted` | #78716C | #9BA1A6 |
| `--accent` (single accent — actions, focus, links) | #2563EB | #60A5FA |
| `--ok` | #15803D | #4ADE80 |
| `--warn` | #B45309 | #FBBF24 |
| `--danger` | #B91C1C | #F87171 |

All pairs meet WCAG AA (≥4.5:1 body text). Semantic colors are reserved for meaning (state, trust) — never decoration. Charts/visualizations follow the `dataviz` skill palette rules.

## Core Components

* **MemoryCard** — title, type badge, summary (2-line clamp), state badge, confidence indicator, relative time. Entire card clickable; ⌘/Ctrl-click opens new pane.
* **StateBadge** — lifecycle state pill. Active=`--ok`, Archived=`--text-muted`, ValidationFailed=`--danger`, transitional states (Validating/Enriching/Updating…)=`--warn` with subtle pulse. Exact state names from `30-memory/03-memory-state-machine.md`.
* **TrustIndicator** — confidence as labeled numeric + 5-segment bar (never color alone); tooltip breaks down evidence count, freshness, verification status; "Why?" link opens ExplainPanel.
* **ExplainPanel** — the signature component. For any retrieved memory: why retrieved, matching criteria, evidence list (linked), confidence, freshness, provenance chain. Directly renders the `/v1/explain` response.
* **LifecycleTimeline** — vertical event history (event type, actor, timestamp, version) from the event log; append-only, newest first.
* **SearchBar** — mode selector (keyword/semantic/hybrid), query, filter chips (namespace, type, state, time range); results always show per-result "Why this result?".
* **VersionSwitcher** — version dropdown on memory detail; older versions clearly watermarked "immutable historical version".
* **EmptyState / ErrorState** — every list and panel has designed empty and error states; errors show `code` + human message + recovery action (retry / docs link), mirroring the API error envelope.

## Accessibility (blocking, not aspirational)

WCAG 2.1 AA. Full keyboard navigation: visible focus ring (`--accent`, 2px offset), logical tab order, `/` focuses search, `Esc` closes panes, roving tabindex in lists. All interactive elements ≥40px hit target. Semantic HTML first, ARIA only where needed. Color never sole information carrier. Screen-reader labels for badges/indicators ("Confidence 0.82, 3 sources, verified").

## Layout

Left nav (Memories · Search · Graph[P4] · Events · Settings) → list pane → detail pane. Detail pane tabs: Overview · Semantics · Relationships · Trust · History. Responsive: panes stack below 900px; console is desktop-first but must not break on tablet.

## Definition of Done (UI work)

Light and dark verified · keyboard-only pass · empty/loading/error states implemented · no layout shift · AA contrast checked · explainability affordance present wherever a memory or search result is shown.
