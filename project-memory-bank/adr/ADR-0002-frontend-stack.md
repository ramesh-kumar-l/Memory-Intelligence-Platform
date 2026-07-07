# ADR-0002: Frontend Stack — React + TypeScript + Vite

**Status:** Accepted
**Date:** 2026-07-07
**Deciders:** Project owner (user), foundation session

## Context

MIP Core needs a developer console (memory explorer with explainability views) that any engineer worldwide can run, trust, and extend. No frontend framework was specified in the specs.

## Decision

The developer console is built with **React + TypeScript (strict) + Vite**, styled per `18-ui-design-system.md` (design tokens, light/dark, WCAG AA). Server state via TanStack Query; API types generated from the backend's OpenAPI schema. It consumes only the public REST API — no privileged backdoors.

## Alternatives Considered

| Option | Why not chosen |
| --- | --- |
| Svelte/SvelteKit | Lighter and elegant, but far smaller contributor pool for a project optimizing for worldwide trust/extension |
| No UI in core (API + CLI only) | Explainability is a core promise; a visual trust surface (Explain panel, lifecycle timeline) materially increases engineer trust |
| Next.js | SSR/server runtime unnecessary for a local console; Vite is simpler (Simplicity Wins) |

## Consequences

* Positive: largest ecosystem/talent pool; first-class TypeScript pairing with the TS SDK; fast local dev.
* Negative / accepted trade-offs: React verbosity vs Svelte; dependency churn risk (mitigated: minimal deps, no UI kit — design system is bespoke tokens/components).
* Follow-ups: console implementation is Phase 3; design system doc already authored.

## Compliance Notes

Console is optional tooling on top of the public API — core platform remains headless and offline-first. Explainability surfaced as a first-class UI concern per Constitution Law on explainability.
