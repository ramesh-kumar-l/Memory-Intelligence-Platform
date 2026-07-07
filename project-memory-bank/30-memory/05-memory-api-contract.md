# 30-memory/05-memory-api-contract.md

**Project:** Memory Intelligence Platform (MIP)

**Document Type:** Canonical Memory API Contract Specification

**Version:** 1.0

**Status:** Draft

**Normative:** YES

**Depends On**

* `30-memory/01-memory-object-model.md`
* `30-memory/02-memory-schema.md`
* `30-memory/03-memory-state-machine.md`
* `30-memory/04-memory-invariants.md`

---

# Executive Summary

This document defines the canonical API semantics for the Memory Intelligence Platform (MIP).

It specifies:

* Public operations
* Behavioral guarantees
* Request semantics
* Response semantics
* Error model
* Idempotency
* Version negotiation
* Compatibility guarantees
* Concurrency behavior

This specification is **transport-independent**.

REST, gRPC, SDKs, CLI, MCP, Android IPC, and future transports SHALL conform to this contract.

---

# Design Principles

The Memory API shall be:

* Stable
* Predictable
* Deterministic
* Explainable
* Idempotent where applicable
* Backward compatible
* Observable
* Storage independent

---

# API Philosophy

Applications interact with **Memory Objects**.

Applications SHALL NOT interact directly with:

* SQL tables
* Graph nodes
* Vector indexes
* Storage engines

The Memory Engine owns those implementation details.

---

# Canonical Operations

The Memory Engine exposes the following logical operations.

## Create

Purpose

Create a new Memory Object.

Operation

```text
CreateMemory
```

Behavior

* Validates schema
* Allocates identity
* Begins lifecycle
* Emits MemoryCreated event

Returns

Memory Object

---

## Read

Purpose

Retrieve a Memory Object.

Operation

```text
GetMemory
```

Behavior

Returns latest active version unless explicitly requested otherwise.

---

## Update

Purpose

Create a newer version.

Operation

```text
UpdateMemory
```

Behavior

Never overwrites previous versions.

Creates a new immutable version.

---

## Delete

Purpose

Delete a Memory Object.

Operation

```text
DeleteMemory
```

Behavior

Transitions lifecycle to Deleted.

Deletion policy depends on deployment mode.

---

## Archive

Purpose

Remove from active retrieval.

Behavior

Memory remains recoverable.

---

## Restore

Purpose

Reactivate archived memory.

---

## Search

Purpose

Retrieve matching Memory Objects.

Search modes include:

* Keyword
* Semantic
* Hybrid
* Graph
* Timeline
* Relationship
* Context

---

## Build Context

Purpose

Generate task-specific context.

Returns

Context Package

---

## Explain

Purpose

Explain why a memory was retrieved.

Returns

* Evidence
* Confidence
* Provenance
* Ranking explanation

---

## Consolidate

Purpose

Merge duplicate memories.

Behavior

Creates new memory relationships.

History preserved.

---

## Learn

Purpose

Update derived semantic knowledge.

Never modifies original evidence.

---

## Export

Purpose

Export Memory Objects.

Supports:

* backup
* migration
* synchronization

---

## Import

Purpose

Import external memories.

Triggers validation pipeline.

---

# Request Semantics

Every request contains:

* request_id
* timestamp
* actor
* API version
* operation
* payload

Optional:

* trace_id
* correlation_id
* session_id

---

# Response Semantics

Every response contains:

* status
* request_id
* processing_time
* schema_version
* result

Optional:

* warnings
* diagnostics
* trace_id

---

# Error Model

Errors SHALL be structured.

Example

```text
Error

Code

Category

Message

Details

Recoverable

Documentation Link
```

Errors SHALL NOT rely solely on human-readable text.

---

# Error Categories

## Validation

Examples

* invalid schema
* missing field
* unsupported version

---

## Lifecycle

Examples

* illegal transition
* deleted object
* archived object

---

## Identity

Examples

* duplicate identity
* unknown identity

---

## Concurrency

Examples

* write conflict
* optimistic lock failure

---

## Trust

Examples

* insufficient evidence
* confidence unavailable

---

## Storage

Examples

* persistence failure
* corruption

---

## Synchronization

Examples

* conflict
* stale version

---

## Authorization

Examples

* permission denied
* ownership violation

---

# Error Codes

Example namespace

```text
MEM-1000 Validation

MEM-2000 Lifecycle

MEM-3000 Identity

MEM-4000 Concurrency

MEM-5000 Trust

MEM-6000 Storage

MEM-7000 Sync

MEM-8000 Security
```

Example

MEM-2004

Illegal Lifecycle Transition

---

# Idempotency

The following operations SHALL be idempotent.

* GetMemory
* Search
* Explain
* Archive
* Restore

DeleteMemory SHALL be idempotent.

Repeated delete returns success.

---

The following operations are NOT idempotent.

* CreateMemory
* UpdateMemory
* Learn

Unless accompanied by an explicit Idempotency Key.

---

# Idempotency Keys

Clients MAY provide:

```text
Idempotency-Key
```

Behavior

Repeated requests with identical key SHALL return the original result.

---

# Concurrency Semantics

Concurrent writes SHALL NOT overwrite committed history.

Possible outcomes

* retry
* merge
* conflict
* version branch (future)

Silent overwrite prohibited.

---

# Pagination

Search responses SHALL support continuation tokens.

Implementations SHALL NOT assume offset-based pagination.

---

# Partial Results

Search MAY return partial results.

Responses SHALL indicate:

* completeness
* continuation token
* warning status

---

# Explainability Contract

Every retrieval SHALL be explainable.

Explain response SHALL include:

* why retrieved
* matching criteria
* evidence
* confidence
* freshness
* provenance

---

# Version Negotiation

Clients specify supported API version.

Server responds with:

* accepted version
* supported versions
* upgrade guidance

Unknown versions SHALL produce explicit negotiation errors.

---

# Backward Compatibility

Minor versions

* additive fields only
* existing behavior preserved

Major versions

May introduce breaking changes.

Require:

* migration guide
* compatibility policy
* deprecation period

---

# Deprecation Policy

Deprecated operations SHALL:

* remain functional during support window
* generate warnings
* include replacement guidance

Silent removal prohibited.

---

# Consistency Guarantees

Read

Consistent snapshot.

Write

Atomic.

Update

Versioned.

Delete

Deterministic.

Replay

Deterministic.

---

# Observability

Every API request SHALL emit:

* trace_id
* latency
* outcome
* request size
* response size

Sensitive payloads SHALL NOT be logged.

---

# Functional Requirements

## FR-API-001

Every transport SHALL preserve API semantics.

Priority

P0

---

## FR-API-002

Every response SHALL include schema version.

Priority

P0

---

## FR-API-003

Errors SHALL be machine-readable.

Priority

P0

---

## FR-API-004

Version negotiation SHALL be explicit.

Priority

P0

---

## FR-API-005

DeleteMemory SHALL be idempotent.

Priority

P0

---

## FR-API-006

UpdateMemory SHALL create new versions.

Priority

P0

---

## FR-API-007

Every retrieval SHALL support Explain.

Priority

P0

---

## FR-API-008

All public operations SHALL generate audit events.

Priority

P0

---

# Acceptance Criteria

An implementation is compliant when:

* Every transport exposes identical logical behavior.
* API semantics are independent of storage implementation.
* Structured errors are returned for all failures.
* Idempotent operations remain safe under retries.
* Concurrent updates preserve history.
* Version negotiation is deterministic.
* Explainability is available for every retrieval.
* Backward compatibility policy is enforced across releases.

---

# Traceability

| Requirement | Capability          | Component             |
| ----------- | ------------------- | --------------------- |
| FR-API-001  | Developer Platform  | API Gateway           |
| FR-API-002  | Versioning          | Schema Manager        |
| FR-API-003  | Reliability         | Error Service         |
| FR-API-004  | Compatibility       | Version Negotiator    |
| FR-API-005  | Lifecycle           | Deletion Service      |
| FR-API-006  | Memory Intelligence | Version Manager       |
| FR-API-007  | Trust Intelligence  | Explainability Engine |
| FR-API-008  | Observability       | Audit Service         |

---

# Future Evolution

The canonical API may later support:

* Streaming memory updates
* Batch transactions
* Event subscriptions
* Multi-agent collaborative operations
* Memory federation
* Policy-aware APIs
* Temporal queries
* Declarative query language

Future extensions must preserve the semantics defined in this specification.

---

# Normative Statement

This API Contract defines the authoritative behavioral semantics for every Memory Intelligence Platform implementation.

Language SDKs, REST APIs, gRPC services, MCP servers, Android bindings, and future transports must implement these semantics without altering their meaning.

Transport technology is replaceable.

API semantics are not.
