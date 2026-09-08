# ADR 001: Transactional Relational State with Append-Only Operational Ledger

## Status
Accepted (Streamlined for Operational MVP)

## Context
High-reliability logistics requires answering two contrasting questions with sub-second performance:
1. **Current Operational Status**: What is the current vehicle status, active stop, and running delay?
2. **Complete Historical Audit**: What exact sequence of events occurred, when did milestones occur, and what manual adjustments were made?

### Evaluation of Pure Event-Sourcing (CQRS / Aggregate Replay)
A pure Event-Sourcing architecture (where the database stores *only* events, and current state is reprojected from the beginning of time or via snapshot streams) was evaluated and **rejected**.
**Reasons for Rejection**:
- Introduces unnecessary architectural bloat for an MVP (projections, eventual consistency, complex schema versioning).
- Complex query overhead for common operational dashboards (e.g., "Find all active vehicles currently in transit").
- High cognitive load and debugging friction for relational data like driver assignments and route stops.

## Decision: Transactional Relational State + Append-Only Ledger
Instead of a complex event-sourcing framework, we adopt the simplest, most reliable relational pattern:
1. **Operational Tables (`trips`, `trip_stops`)**: Store current mutable state (`status`, `actual_arrival`, `actual_departure`, `total_delay_minutes`) for instant, indexed relational queries and dashboards.
2. **Append-Only Ledger (`trip_events`)**: Every operational milestone (`TRIP_STARTED`, `ARRIVED_AT_STOP`, `DEPARTED_STOP`, `INCIDENT_REPORTED`, `MANUAL_CORRECTION`) appends an immutable row with timestamps, source, and notes.
3. **Atomic Transactions**: Operational table updates and event row insertions occur within the **same PostgreSQL ACID transaction**. If the event log insertion fails, the status update rolls back.
4. **Audit Trail (`audit_logs`)**: Dedicated forensic table capturing all manual manager modifications (old value, new value, user, mandatory reason).

## Consequences
### Positive
- **Simplicity & Reliability**: Standard PostgreSQL relational integrity, standard SQLAlchemy 2.0 ORM, and immediate consistency.
- **Zero Historical Data Loss**: Operational timeline is 100% preserved as an immutable stream.
- **Sub-Millisecond Dashboard Performance**: Instant queries via standard B-Tree indexes (`SELECT * FROM trips WHERE status = 'IN_TRANSIT'`).
- **Zero Event-Sourcing Bloat**: No distributed event brokers, no separate read/write databases, no eventual consistency lag.

### Negative
- Operational state changes require dual writes (state row + event row). In PostgreSQL, this overhead is negligible (sub-millisecond) within a local transaction.
