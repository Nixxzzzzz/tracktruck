# ADR 002: Offline-First Mobile Event Synchronization & Idempotency

## Status
Accepted

## Context
Commercial drivers travel across national highways, industrial zones, and rural transit points with prolonged cellular dead-zones. A driver must be able to record stop arrivals, departures, loading progress, and incident reports without waiting for network connectivity.

When connectivity is restored, sending batches of events introduces risks of:
1. **Duplicate Processing**: Network timeout during response causes the mobile client to retry the request.
2. **Out-of-Order Execution**: Arrived and departed events may arrive simultaneously or out of sequence.
3. **Clock Discrepancies**: The mobile client's system clock may differ from the server's authoritative clock.

## Decision
We implement a **Client-Side Outbox Queue + Deterministic Idempotency Key** architecture:
1. **Local Storage**: The Flutter Android application writes all driver actions immediately to a local SQLite database (via Drift) with status `PENDING` and a client-side UUID.
2. **Deterministic Keys**: Every event computes a unique `idempotency_key = SHA256(trip_id + stop_id + event_type + client_seq)`.
3. **Server Ingestion**: The backend checks for key existence. Duplicates return HTTP `200 OK` without re-executing state transitions.
4. **Clock Skew Tolerance**: The server accepts client recorded timestamps within a 15-minute window; larger variances are flagged for supervisor review but never dropped.

## Consequences
### Positive
- Zero data loss in the field. Drivers never encounter network-blocked blocking spinners.
- Complete protection against duplicate arrivals and phantom stops.
- Reliable sync recovery once connectivity is re-established.

### Negative
- Local database management and migration logic is required on the Flutter client. Drift provides compile-time query safety to mitigate schema drift.
