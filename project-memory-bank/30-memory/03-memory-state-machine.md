# 30-memory/03-memory-state-machine.md

**Project:** Memory Intelligence Platform (MIP)

**Document Type:** Memory Lifecycle State Machine Specification

**Version:** 1.0

**Status:** Draft

**Normative:** YES

**Depends On**

* `30-memory/01-memory-object-model.md`
* `30-memory/02-memory-schema.md`

---

# Executive Summary

Every Memory Object in the Memory Intelligence Platform (MIP) progresses through a well-defined lifecycle.

This document specifies:

* lifecycle states
* legal transitions
* transition triggers
* failure states
* recovery procedures
* invariants
* concurrency rules

Every implementation MUST conform to this lifecycle.

---

# Design Goals

The lifecycle shall be:

* Deterministic
* Replayable
* Observable
* Recoverable
* Versioned
* Auditable
* Storage-independent

---

# State Machine Philosophy

A Memory Object never changes arbitrarily.

Every state transition:

* has a reason
* has a trigger
* produces an audit event
* is replayable
* can be explained

---

# Lifecycle Overview

```text id="lifecyclesm"
                +----------------+
                |   Created      |
                +----------------+
                         |
                         v
                +----------------+
                |   Validating   |
                +----------------+
                  |           |
          success |           | failure
                  v           v
          +---------------+  +------------------+
          | Validated     |  | ValidationFailed |
          +---------------+  +------------------+
                  |
                  v
           +---------------+
           |  Enriching    |
           +---------------+
                  |
                  v
           +---------------+
           |   Indexed     |
           +---------------+
                  |
                  v
           +---------------+
           | GraphLinked   |
           +---------------+
                  |
                  v
           +---------------+
           |    Active     |
           +---------------+
            |      |      |
            |      |      |
      update| archive|delete
            |      |      |
            v      v      v
     +-------------+  +-----------+
     | Updating    |  | Archived  |
     +-------------+  +-----------+
            |
            v
         Active

Deleted is terminal.
```

---

# Lifecycle States

## CREATED

### Purpose

Memory Object has been allocated but not yet validated.

### Allowed Operations

* Read metadata
* Validate
* Reject

### Forbidden Operations

* Retrieval
* Search
* Context generation

---

## VALIDATING

### Purpose

Schema and semantic validation are running.

Checks include:

* required fields
* schema
* ownership
* integrity
* semantic consistency

---

## VALIDATION_FAILED

### Purpose

Validation failed.

Reasons

* invalid schema
* corrupted payload
* missing required fields
* invalid references

Allowed transitions

* Retry Validation
* Delete

---

## VALIDATED

Memory is structurally correct.

Not yet searchable.

---

## ENRICHING

Platform performs:

* embeddings
* entity extraction
* OCR
* graph preparation
* trust estimation
* duplicate detection

This state may be asynchronous.

---

## INDEXED

Memory available for search.

Graph not yet connected.

---

## GRAPH_LINKED

Relationships established.

Graph consistency verified.

---

## ACTIVE

Normal operating state.

Memory participates in:

* retrieval
* context generation
* graph traversal
* learning
* synchronization

---

## UPDATING

New version is being created.

Important

Original version remains immutable.

---

## ARCHIVED

Memory retained.

No longer actively retrieved.

Still queryable when requested.

---

## DELETED

Terminal state.

No further transitions allowed.

Deletion policy depends on deployment mode.

---

# State Definitions

| State            | Searchable | Mutable          | Recoverable |
| ---------------- | ---------- | ---------------- | ----------- |
| Created          | No         | Yes              | Yes         |
| Validating       | No         | No               | Yes         |
| ValidationFailed | No         | Limited          | Yes         |
| Validated        | No         | Limited          | Yes         |
| Enriching        | No         | No               | Yes         |
| Indexed          | Yes        | Limited          | Yes         |
| GraphLinked      | Yes        | Limited          | Yes         |
| Active           | Yes        | New Version Only | Yes         |
| Updating         | Yes        | New Version Only | Yes         |
| Archived         | Optional   | No               | Yes         |
| Deleted          | No         | No               | No          |

---

# Legal State Transitions

| From             | To               |
| ---------------- | ---------------- |
| Created          | Validating       |
| Validating       | Validated        |
| Validating       | ValidationFailed |
| ValidationFailed | Validating       |
| Validated        | Enriching        |
| Enriching        | Indexed          |
| Indexed          | GraphLinked      |
| GraphLinked      | Active           |
| Active           | Updating         |
| Updating         | Active           |
| Active           | Archived         |
| Archived         | Active           |
| Active           | Deleted          |

All other transitions are illegal.

---

# Illegal Transitions

Examples

Deleted → Active

Created → Active

ValidationFailed → Indexed

Archived → Enriching

Implementations MUST reject illegal transitions.

---

# Transition Triggers

| Trigger            | Transition                    |
| ------------------ | ----------------------------- |
| create             | Created                       |
| validate           | Created → Validating          |
| validation success | Validating → Validated        |
| validation error   | Validating → ValidationFailed |
| enrich             | Validated → Enriching         |
| indexing complete  | Enriching → Indexed           |
| graph complete     | Indexed → GraphLinked         |
| activation         | GraphLinked → Active          |
| update             | Active → Updating             |
| publish            | Updating → Active             |
| archive            | Active → Archived             |
| restore            | Archived → Active             |
| delete             | Active → Deleted              |

---

# Failure States

Failure is explicit.

Failures are not hidden.

Examples

Validation Failure

Embedding Failure

Graph Failure

Storage Failure

Synchronization Failure

Trust Computation Failure

Each failure produces:

* error code
* audit event
* retry policy
* diagnostics

---

# Recovery Behavior

Validation Failure

Recovery

Retry validation after correction.

---

Embedding Failure

Recovery

Retry enrichment.

Memory remains unavailable until enrichment succeeds.

---

Graph Failure

Recovery

Retry graph linking.

Search remains available if indexing succeeded.

---

Synchronization Failure

Recovery

Queue synchronization.

Memory remains locally active.

---

Storage Failure

Recovery

Rollback transaction.

Restore previous consistent version.

---

# Concurrency Rules

Only one lifecycle transition may execute at a time.

Concurrent updates create:

new versions

never overwrite existing versions.

Conflict resolution occurs during synchronization.

---

# Lifecycle Events

Every transition emits an immutable event.

Example

MemoryCreated

MemoryValidated

MemoryIndexed

MemoryActivated

MemoryUpdated

MemoryArchived

MemoryDeleted

Events are append-only.

---

# Replayability

The complete lifecycle shall be reconstructable from events.

Example

```text id="replay"
Created

↓

Validated

↓

Enriched

↓

Indexed

↓

GraphLinked

↓

Activated

↓

Updated

↓

Archived
```

Replay must produce identical state.

---

# Functional Requirements

## FR-LIFE-001

Every Memory Object shall begin in Created.

Priority

P0

---

## FR-LIFE-002

Only legal transitions shall be permitted.

Priority

P0

---

## FR-LIFE-003

Every transition shall emit an audit event.

Priority

P0

---

## FR-LIFE-004

Transitions shall be deterministic.

Priority

P0

---

## FR-LIFE-005

Deleted state is terminal.

Priority

P0

---

## FR-LIFE-006

Updating shall create a new version.

Priority

P0

---

## FR-LIFE-007

Recovery procedures shall preserve data integrity.

Priority

P0

---

# Acceptance Criteria

A lifecycle implementation is compliant when:

* Illegal transitions are rejected.
* Every transition is logged.
* Replay reconstructs identical state.
* Recovery procedures preserve consistency.
* Version history remains intact.
* Deleted objects cannot be reactivated.
* Concurrency conflicts do not corrupt memory history.

---

# Traceability

| Requirement | Capability          | Architecture            |
| ----------- | ------------------- | ----------------------- |
| FR-LIFE-001 | Memory Intelligence | Lifecycle Manager       |
| FR-LIFE-002 | Memory Intelligence | State Machine Engine    |
| FR-LIFE-003 | Audit               | Event Store             |
| FR-LIFE-004 | Reliability         | Transition Manager      |
| FR-LIFE-005 | Memory Lifecycle    | Deletion Service        |
| FR-LIFE-006 | Versioning          | Version Manager         |
| FR-LIFE-007 | Recovery            | Transaction Coordinator |

---

# Future Evolution

Future versions may introduce:

* Distributed lifecycle coordination
* Multi-region synchronization states
* Human approval workflows
* Policy-controlled transitions
* Collaborative editing states
* AI-assisted conflict resolution

These extensions must preserve the deterministic lifecycle defined in this specification.

---

# Normative Statement

The lifecycle defined in this document is the authoritative behavioral model for every Memory Object in the Memory Intelligence Platform.

All storage engines, APIs, SDKs, synchronization mechanisms, and user interfaces must conform to this state machine.

No implementation may introduce undocumented lifecycle states or transition paths without:

1. Updating this specification.
2. Creating an approved Architecture Decision Record (ADR).
3. Providing backward compatibility guidance.
