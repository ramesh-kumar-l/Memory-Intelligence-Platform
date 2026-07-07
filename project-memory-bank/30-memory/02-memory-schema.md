# 30-memory/02-memory-schema.md

**Project:** Memory Intelligence Platform (MIP)

**Document Type:** Canonical Memory Schema Specification

**Version:** 1.0

**Status:** Draft

**Normative:** YES

**Depends On**

* `00-vision.md`
* `PRD/00-PRD-Overview.md`
* `30-memory/01-memory-object-model.md`

---

# Canonical Memory Schema

## Executive Summary

This document defines the canonical schema for the Memory Object used throughout the Memory Intelligence Platform (MIP).

The schema is **technology-independent**.

It does **not** prescribe:

* database schema
* ORM models
* protobuf definitions
* JSON serialization
* Graph schema
* Vector schema

Instead, it defines the logical contract that every implementation SHALL satisfy.

---

# Goals

The schema must be:

* Stable
* Versioned
* Extensible
* Language-neutral
* Storage-neutral
* Backward compatible
* Explainable
* Privacy-aware

---

# Design Principles

## Schema First

Every subsystem consumes the same logical schema.

---

## Storage Independence

SQLite, PostgreSQL, Neo4j, Qdrant and future storage engines are implementation details.

---

## Forward Compatibility

New fields must never require existing clients to break.

---

## Backward Compatibility

Removing required fields is prohibited.

---

# Canonical Memory Object

A Memory Object consists of eleven logical sections.

```text
MemoryObject

├── Header
├── Identity
├── Content
├── Semantics
├── Relationships
├── Context
├── Trust
├── Lifecycle
├── Storage Metadata
├── Extension Data
└── Audit Metadata
```

---

# Section 1 — Header

Purpose:

Provides metadata required for serialization and compatibility.

| Field            | Type   | Required | Description               |
| ---------------- | ------ | -------- | ------------------------- |
| schema_version   | String | Yes      | Schema version identifier |
| object_type      | Enum   | Yes      | Memory type               |
| encoding_version | String | Yes      | Serialization version     |
| checksum         | String | Optional | Integrity validation      |

---

# Section 2 — Identity

Purpose:

Defines immutable identity.

| Field           | Type   | Required |
| --------------- | ------ | -------- |
| memory_id       | UUID   | Yes      |
| namespace       | String | Yes      |
| owner_id        | String | Yes      |
| tenant_id       | String | Optional |
| parent_id       | UUID   | Optional |
| root_episode_id | UUID   | Optional |

Rules

* memory_id never changes
* namespace immutable
* owner immutable

---

# Section 3 — Content

Purpose

Human-readable knowledge.

| Field       | Type   |
| ----------- | ------ |
| title       | String |
| summary     | String |
| description | String |
| language    | String |
| attachments | Array  |
| media_refs  | Array  |
| notes       | Array  |

Rules

Title should be concise.

Summary should fit within configured limits.

Description may be large.

---

# Section 4 — Semantic Layer

Purpose

Machine-readable understanding.

| Field      | Type   |
| ---------- | ------ |
| entities   | Array  |
| concepts   | Array  |
| activities | Array  |
| events     | Array  |
| locations  | Array  |
| topics     | Array  |
| timestamps | Array  |
| keywords   | Array  |
| sentiment  | Object |
| intent     | Object |

Requirements

Every Memory Object must contain at least one semantic element.

---

# Section 5 — Relationships

Purpose

Connect memory to other memories.

Relationship Object

| Field            | Type      |
| ---------------- | --------- |
| relationship_id  | UUID      |
| target_memory_id | UUID      |
| type             | Enum      |
| direction        | Enum      |
| confidence       | Float     |
| created_at       | Timestamp |

Relationship Types

* contains
* references
* duplicate_of
* derived_from
* related_to
* occurred_before
* occurred_after
* caused_by
* supports
* contradicts
* supersedes

Future relationship types must remain backward compatible.

---

# Section 6 — Context

Purpose

Contextual information used during retrieval.

| Field            | Type      |
| ---------------- | --------- |
| importance_score | Float     |
| recency_score    | Float     |
| access_frequency | Integer   |
| last_accessed    | Timestamp |
| relevance_tags   | Array     |
| goals            | Array     |

Context changes frequently.

It is not immutable.

---

# Section 7 — Trust

Purpose

Describe confidence and explainability.

| Field               | Type    |
| ------------------- | ------- |
| confidence          | Float   |
| freshness           | Float   |
| provenance          | Object  |
| evidence            | Array   |
| verification_status | Enum    |
| source_count        | Integer |
| explanation         | String  |

Trust scores are derived.

Raw evidence is authoritative.

---

# Section 8 — Lifecycle

Purpose

Track evolution.

| Field               | Type      |
| ------------------- | --------- |
| version             | Integer   |
| state               | Enum      |
| created_at          | Timestamp |
| updated_at          | Timestamp |
| archived_at         | Timestamp |
| deleted_at          | Timestamp |
| consolidation_count | Integer   |

Allowed States

* Created
* Validated
* Indexed
* Active
* Updated
* Archived
* Deleted

Only one Active version is allowed.

---

# Section 9 — Storage Metadata

Purpose

Support persistence implementations.

| Field          | Type   |
| -------------- | ------ |
| storage_engine | String |
| partition      | String |
| shard          | String |
| vector_id      | String |
| graph_node_id  | String |
| blob_refs      | Array  |

Important

Applications must never depend upon these identifiers.

---

# Section 10 — Extension Data

Purpose

Future-proofing.

| Field      | Type               |
| ---------- | ------------------ |
| extensions | Map<String,Object> |

Rules

Unknown extensions shall be ignored by compliant clients.

Extension namespaces should avoid collisions.

---

# Section 11 — Audit Metadata

Purpose

Support replayability and debugging.

| Field         | Type   |
| ------------- | ------ |
| created_by    | String |
| updated_by    | String |
| update_reason | String |
| change_set    | String |
| trace_id      | String |
| request_id    | String |

Audit history must remain append-only.

---

# Required Fields

Every valid Memory Object SHALL contain:

* schema_version
* object_type
* memory_id
* namespace
* owner_id
* title
* version
* state
* created_at
* confidence
* provenance
* at least one semantic element

Objects missing required fields are invalid.

---

# Optional Fields

Optional fields may be omitted when unavailable.

Clients must tolerate absent optional fields.

---

# Enumerations

## Memory Types

* Experience
* Episode
* Semantic
* Relationship
* Context
* Working
* Learned
* System

---

## Lifecycle States

* Created
* Validated
* Indexed
* Active
* Updated
* Archived
* Deleted

---

## Verification Status

* Unknown
* Unverified
* PartiallyVerified
* Verified
* Disputed

---

# Validation Rules

## Identity

* UUID format required
* Immutable after creation

---

## Content

* Title cannot be empty
* Description optional

---

## Trust

* Confidence range 0.0–1.0
* Freshness range 0.0–1.0

---

## Relationships

Target Memory must exist unless marked unresolved.

---

## Version

Version must increase monotonically.

---

# Functional Requirements

### FR-SCHEMA-001

Every Memory Object shall conform to this canonical schema.

Priority

P0

---

### FR-SCHEMA-002

Implementations shall reject invalid required fields.

Priority

P0

---

### FR-SCHEMA-003

Unknown extension fields shall not invalidate the object.

Priority

P1

---

### FR-SCHEMA-004

Schema evolution shall preserve backward compatibility.

Priority

P0

---

### FR-SCHEMA-005

Serialization format shall not change logical meaning.

Priority

P0

---

# Acceptance Criteria

A schema implementation is compliant when:

* Every required field validates successfully.
* Invalid objects are rejected with structured validation errors.
* Optional fields remain interoperable.
* Schema version is preserved across serialization and deserialization.
* Unknown extensions are safely ignored or preserved according to implementation policy.
* Logical equality is maintained regardless of storage engine or transport format.

---

# Traceability

| Requirement   | Capability           | Future Architecture |
| ------------- | -------------------- | ------------------- |
| FR-SCHEMA-001 | Memory Intelligence  | Memory Engine       |
| FR-SCHEMA-002 | Memory Intelligence  | Validation Service  |
| FR-SCHEMA-003 | Extensibility        | Plugin Framework    |
| FR-SCHEMA-004 | Platform Stability   | API Versioning      |
| FR-SCHEMA-005 | Storage Independence | Serialization Layer |

---

# Future Evolution

The canonical schema is expected to evolve through additive changes only.

Potential future additions include:

* Distributed ownership metadata
* Federated memory references
* Agent collaboration metadata
* Policy annotations
* Temporal validity windows
* Semantic embedding descriptors
* Regulatory compliance metadata

Breaking changes require:

1. A new schema version.
2. A documented migration strategy.
3. Backward compatibility guidance.
4. An approved Architecture Decision Record (ADR).

---

# Implementation Guidance

The canonical schema is the **single source of truth** for every Memory Object implementation.

All language bindings (Python, Kotlin, TypeScript, Rust, Go, Swift) and all persistence layers (SQL, graph, vector, object storage) must map to this logical model without changing its semantics.

No implementation may introduce behavior that contradicts this specification.
