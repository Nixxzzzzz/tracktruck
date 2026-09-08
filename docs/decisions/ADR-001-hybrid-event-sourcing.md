# ADR 001: Hybrid Event Sourcing & Relational State

## Status
Accepted

## Context
High-reliability logistics requires answering two contrasting questions with sub-second performance:
1. **Current Operational Status**: What is the current vehicle position, current stop, and active delay?
2. **Complete Historical Audit**: What exact sequence of events occurred, who authorized manual adjustments, and what were the exact milestone timestamps?

A purely mutable CRUD approach overwrites history, violating compliance, auditability, and delay analysis requirements. Conversely, a pure event-sourcing model (e.g. CQRS + EventStore) introduces excessive read-side projection complexity for a standard relational platform.

## Decision
We adopt a **Hybrid Event Sourcing Architecture** backed by PostgreSQL 16:
- **Mutable Operational Views** (`trips`, `trip_stops`): Store current state, active milestone, and pre-aggregated delay metrics for fast operational querying.
- **Append-Only Event Store** (`trip_events`): Every status transition, arrival, loading milestone, and departure writes an immutable record with timestamps, source, and payload.
- **Audited Manager Modifications** (`audit_logs`): When a manager updates an operational record, a mandatory reason is captured, old/new states are preserved in `audit_logs`, and the original `trip_events` history is never erased.

## Consequences
### Positive
- Sub-millisecond performance on operational dashboards (`SELECT * FROM trips WHERE status = 'IN_TRANSIT'`).
- 100% forensic auditability for dispute resolution, insurance claims, and SLA enforcement.
- Built-in readiness for future machine-learning models predicting route delays.

### Negative
- State updates require database transactions touching both operational tables and the event table. This is mitigated by PostgreSQL's high-throughput row-level ACID transactions.
