# Mobile Architecture & Offline Synchronization

## 1. Mobile Terminal Overview

The driver field terminal is built with **Flutter / Dart** and engineered specifically for commercial drivers operating in remote corridors with unstable or zero cellular network coverage.

```mermaid
flowchart TD
    subgraph UI["Driver Touch Interface"]
        TodayTripScreen["Today's Active Trip (Hero View)"]
        LargeActionBtn["Tactile Milestone Buttons\n(ARRIVED, START LOADING, DEPARTED)"]
        DelayModal["Single-Tap Delay Root-Cause Selector"]
        IncidentModal["Emergency Breakdown / Accident Reporter"]
    end

    subgraph LocalStorage["Local SQLite Engine (Drift)"]
        LocalTripsTable[("Local Trips Cache")]
        LocalStopsTable[("Local Stops Cache")]
        SyncQueue[("Outbox Sync Queue\n(Status: PENDING, SYNCING, SYNCED)")]
    end

    subgraph SyncEngine["Background Sync Engine"]
        NetListener["Connectivity Broadcast Listener"]
        BatchWorker["Idempotent HTTP Batch Dispatcher"]
    end

    subgraph CloudAPI["FastAPI Authoritative Backend"]
        SyncEndpoint["POST /api/v1/trips/events/sync"]
        PostgresCore[("PostgreSQL 16 Authoritative DB")]
    end

    LargeActionBtn -->|Write Event Locally| SyncQueue
    DelayModal -->|Attach Reason| SyncQueue
    IncidentModal -->|Write Incident| SyncQueue

    SyncQueue --> BatchWorker
    NetListener -->|Trigger on Reconnect| BatchWorker
    BatchWorker -->|Bearer JWT + Idempotency Keys| SyncEndpoint
    SyncEndpoint --> PostgresCore
    SyncEndpoint -->>|Ack Success| BatchWorker
    BatchWorker -->|Update Status: SYNCED| SyncQueue
```

---

## 2. Deterministic Idempotency & De-duplication

To eliminate duplicate event ingestion caused by cellular dropouts during HTTP round-trips, every mobile event generates a deterministic **Idempotency Key**:

$$\mathbf{IdempotencyKey} = \text{SHA256}(\text{trip\_id} + \text{stop\_id} + \text{event\_type} + \text{client\_sequence\_no})$$

### Server Ingestion Logic:
1. Server receives payload containing `idempotency_key`.
2. Checks if `idempotency_key` already exists in `trip_events`.
3. If it exists:
   - Returns HTTP `200 OK` with the previously created record.
   - Does **not** insert a duplicate event or re-execute side effects.
4. If new:
   - Executes state transition inside a database transaction.
   - Inserts `trip_events` record with the key.
   - Returns HTTP `201 Created`.

---

## 3. Local SQLite Schema (Drift Definition)

```dart
// Drift Schema Definition for Local Outbox Queue
class LocalSyncEvents extends Table {
  TextColumn get eventId => text()(); // UUID v4
  TextColumn get tripId => text()();
  TextColumn get stopId => text().nullable()();
  TextColumn get eventType => text()(); // ARRIVED_AT_STOP, DEPARTED_STOP, etc.
  DateTimeColumn get clientTimestamp => dateTime()();
  TextColumn get delayType => text().nullable()();
  TextColumn get reason => text().nullable()();
  TextColumn get idempotencyKey => text()();
  TextColumn get syncStatus => text().withDefault(const Constant('PENDING'))(); // PENDING, SYNCING, SYNCED
  IntColumn get retryCount => integer().withDefault(const Constant(0))();
  DateTimeColumn get lastAttempt => dateTime().nullable()();

  @override
  Set<Column> get primaryKey => {eventId};
}
```

---

## 4. Clock Skew Protection & Reconciliation

Driver smartphones may have incorrect local clock settings, timezone discrepancies, or deliberate manual adjustments.

The server reconciles timestamps through the following algorithm:
1. Event payload sends:
   - `client_recorded_at`: Local device hardware time.
   - `client_uptime_ms`: System uptime duration since boot.
2. Server verifies variance:
   $$\Delta T = |T_{\text{server\_received}} - T_{\text{client\_recorded}}|$$
3. If $\Delta T \le 15 \text{ minutes}$:
   - Server honors `client_recorded_at` for operational variance calculations.
4. If $\Delta T > 15 \text{ minutes}$:
   - Event is accepted to preserve driver workflow.
   - Event is tagged with `flag: CLOCK_SKEW_DETECTED`.
   - Supervisor is notified in the Operations Console for manual time audit verification.

---

## 5. Driver Tactical Ergonomics

- **Oversized Touch Targets**: Buttons have a minimum height of 64dp to permit accurate tapping even while wearing work gloves.
- **High Visual Contrast**: Pure black (`#0B0C0E`) with vivid off-white text and gold accents ensures direct sunlight readability in the truck cabin.
- **Single-Hand Workflow**: Primary operational actions are anchored to the lower third of the screen.
