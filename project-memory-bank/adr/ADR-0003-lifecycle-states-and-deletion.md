# ADR-0003: Lifecycle State Enum Resolution & Phase 1 Deletion Policy

**Status:** Accepted
**Date:** 2026-07-07
**Deciders:** Project owner (user), Phase 1 kickoff ("continue with Phase 1" after the recommendation was documented in `29-session-handoff.md`)

## Context

Two normative specs disagree: `30-memory/02-memory-schema.md` lists 7 lifecycle states; `30-memory/03-memory-state-machine.md` (the behavioral spec) defines 11 (`Created, Validating, ValidationFailed, Validated, Enriching, Indexed, GraphLinked, Active, Updating, Archived, Deleted`) plus a 13-row legal-transition table. Deletion semantics are also deferred by the specs to "deployment mode".

## Decision

1. The **state machine spec is authoritative**: the runtime lifecycle enum has the 11 states and exactly the 13 legal transitions. The schema doc's 7-state list is treated as an outdated subset needing an additive spec update (its `Updated` corresponds to `Updating`).
2. **Deletion is tombstone by default** in local deployment: the projection row is retained with `state=Deleted` + `deleted_at`; events are never removed; deleted memory content is no longer served by any endpoint (`MEM-2003`/410). Hard purge is a future, explicitly-invoked operation.
3. Only `Active → Deleted` is legal (per the transition table). Deleting an `Archived` memory requires restore first; the prose "ValidationFailed allows Delete" is *not* implemented because the table says "all other transitions are illegal" — table wins.

## Alternatives Considered

| Option | Why not chosen |
| --- | --- |
| Schema's 7 states authoritative | Loses failure/enrichment observability; contradicts the behaviorally normative transition table |
| Hard delete by default | Violates event immutability and audit replayability; tombstone preserves both while hiding content |
| Allow Delete from any state | Contradicts the normative transition table; would need a spec change + ADR first |

## Consequences

* Positive: deterministic, replayable lifecycle exactly as specified; audit history survives deletion.
* Negative / accepted trade-offs: schema spec temporarily inconsistent until additively updated; archived memories need two calls to delete.
* Follow-ups: additive update to `30-memory/02-memory-schema.md` state enum (pending user edit of the normative spec).

## Compliance Notes

Backward compatible (7 old states are a subset of 11). Preserves event append-only law, INV-STATE-002/003, and privacy-by-default (deleted content not served).
