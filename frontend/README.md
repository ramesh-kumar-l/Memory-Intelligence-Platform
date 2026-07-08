# MIP Console — Developer Console

Explainability-first developer console for the Memory Intelligence Platform: memory
explorer, search with per-result "why", lifecycle/trust panels. React + TypeScript +
Vite, built on `@mip/sdk`. Design system: `../project-memory-bank/18-ui-design-system.md`.

## Quickstart

```bash
# from the repo root — links this package to sdk/typescript via npm workspaces
npm install
npm run build --workspace=@mip/sdk

cd frontend
npm run dev              # http://localhost:5173, defaults to http://localhost:8000
```

Set the API URL either via `VITE_MIP_API_URL` (build/dev time) or in the console's own
Settings page (persisted to `localStorage`, takes precedence).

## Pages

* **Memories** — list (namespace filter) + detail pane (Overview · Semantics ·
  Relationships · Trust · History tabs), archive/restore/delete actions.
* **Search** — keyword/semantic/hybrid, per-result "Why this result?" opens the
  ExplainPanel.
* **Settings** — configure and test the API connection.

Graph (Phase 4) and a global Events feed are intentionally not in the nav — Graph has
no API surface yet, and per-memory history is covered by the detail pane's History tab
instead of a separate global event log endpoint (none exists in Phase 1/2).

## Accessibility & theming

WCAG AA, full keyboard support (`/` focuses search, `Esc` closes the detail pane,
visible focus rings, ≥40px hit targets), light/dark via `prefers-color-scheme` with a
manual override in the top bar.

## Quality gates (all must pass)

```bash
npm run lint
npm run typecheck
npm test          # vitest + Testing Library, jsdom
npm run build
```
