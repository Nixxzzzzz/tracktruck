# System Architecture Specification

## 1. System Overview

AURELIS FLEET is designed as a high-reliability, multi-tier distributed logistics platform. The platform decouples presentation clients from the business and data tiers, routing all traffic through a centralized, secured API gateway.

```mermaid
flowchart TD
    subgraph Presentation["Presentation Tier"]
        Web["Web Application\n(Next.js 14 App Router / TypeScript)\nRole: Command Center & Dispatch"]
        Mobile["Android Field Terminal\n(Flutter / Drift SQLite)\nRole: Driver Milestone Recording"]
    end

    subgraph SecurityBoundary["Gateway & Reverse Proxy Tier"]
        Proxy["Nginx / Traefik (TLS Termination, Rate Limiting)"]
        AuthMiddleware["FastAPI Security & RBAC Middleware"]
    end

    subgraph ServiceLayer["Core Application Tier (FastAPI / Python 3.12)"]
        AuthService["Auth & Session Service"]
        MasterDataService["Master Data Engine (Vehicles, Drivers, Hubs)"]
        TripEngine["Trip Planning & Dispatch Engine"]
        StateMachine["State Machine & Validation Engine"]
        EventService["Append-Only Event Store Service"]
        VarianceService["Planned-vs-Actual Variance Calculator"]
        SyncService["Idempotent Offline Sync Orchestrator"]
        AuditService["Operational Audit Trail Service"]
        ReportingEngine["Analytical Reporting Engine"]
    end

    subgraph PersistenceTier["Data & Cache Tier"]
        Postgres[(PostgreSQL 16 Enterprise Database\nACID Relational Core)]
        Redis[(Redis 7 In-Memory Cache\nToken Revocation, Locks & Rate Limiting)]
        MinIO[(S3-Compatible Object Store\nDocuments, Waybills, Damage Photos)]
    end

    Web -->|HTTPS / JSON / WebSocket| Proxy
    Mobile -->|HTTPS / JSON / Offline Batch| Proxy
    Proxy --> AuthMiddleware
    AuthMiddleware --> ServiceLayer

    ServiceLayer --> Postgres
    ServiceLayer --> Redis
    ServiceLayer --> MinIO
```

---

## 2. Tier Responsibilities & Structural Decomposition

### 2.1 Web Application Tier (`/apps/web`)
- **Technology**: Next.js 14 (App Router), React 18, TypeScript 5, Tailwind CSS.
- **Audience**: Super Admins, Operations Admins, Fleet Managers, Depot Supervisors.
- **Key Modules**:
  - `Operations Control Center`: Real-time active trip cards, live route milestones, delayed vehicle alerts.
  - `Trip Planner`: Multi-stop route sequencer, route template loader, payload manifest assignment.
  - `Trip Detail`: Granular timeline visualizer, planned vs. actual variance matrix, incident logs, manager audit panel.
  - `Master Registries`: Vehicles, drivers, materials, locations, and route templates.
  - `Reports & Analytics`: Utilization curves, delay Pareto analysis, driver punctuality ratings.
- **Design Philosophy**: Luxury automotive dark mode (`#0B0C0E` background, `#C8A96B` champagne gold accents, typography inspired by luxury instrumentation).

### 2.2 Mobile Field Terminal Tier (`/apps/mobile`)
- **Technology**: Flutter 3.22+, Dart 3.4+, Drift (SQLite local storage).
- **Audience**: Commercial Fleet Drivers.
- **Key Capabilities**:
  - Tactile, oversized touch targets for rapid single-tap milestone reporting (`ARRIVED`, `START LOADING`, `DEPARTED`).
  - Strict offline-first architecture with persistent local queuing.
  - Zero cognitive friction: driver is presented only with current leg actions and emergency incident reporting.

### 2.3 Application Core & Service Tier (`/backend`)
- **Technology**: FastAPI (Python 3.12), Pydantic v2, SQLAlchemy 2.0, Alembic.
- **Architectural Rules**:
  - **Zero Business Logic in HTTP Controllers**: Routes are pure thin translation layers; all business rules, state validations, and transactions live in `/app/services/`.
  - **Append-Only Event Sourcing Pattern**: Operational state updates produce immutable event rows in `trip_events`.
  - **Transaction Boundary**: Trip lifecycle mutations execute in explicit PostgreSQL transactions with rollback safety.

### 2.4 Persistence & Cache Tier
- **PostgreSQL 16**: Primary source of truth with strict foreign keys, composite indexes, and check constraints.
- **Redis 7**: Distributed rate limiting, active token tracking, and distributed locks for state transition synchronization.
- **MinIO / AWS S3**: Object store for bill of lading (BOL), vehicle fitness certificates, and driver license photos.

---

## 3. Data Flow Architecture: End-to-End Operational Lifecycle

The diagram below illustrates how an operational milestone recorded in the field flows into the database, updates current state, and is reflected on executive dashboards:

```mermaid
sequenceDiagram
    autonumber
    actor Driver as Driver (Field)
    participant Mobile as Android App (Local SQLite)
    participant Gateway as API Gateway
    participant EventSvc as Event Service
    participant TripEngine as Trip State Engine
    participant DB as PostgreSQL Core
    participant Cache as Redis
    actor Manager as Fleet Manager (Console)

    Driver->>Mobile: Taps "ARRIVED" at Indore Depot
    Mobile->>Mobile: Insert local event (UUID, timestamp, PENDING)
    Mobile->>Gateway: POST /api/v1/trips/{id}/events (Bearer Token + Idempotency Key)
    Gateway->>EventSvc: Validate token & idempotency key
    EventSvc->>Cache: Acquire distributed lock for trip_id
    EventSvc->>TripEngine: Validate transition (IN_TRANSIT -> ARRIVED)
    TripEngine->>TripEngine: Calculate arrival variance (Actual vs Planned)
    
    critical Database Transaction
        EventSvc->>DB: Insert into trip_events (Immutable)
        TripEngine->>DB: Update trip_stops (actual_arrival, delay_minutes, status=ARRIVED)
        TripEngine->>DB: Update trips (status=ARRIVED, total_delay_minutes)
    end
    
    EventSvc->>Cache: Release distributed lock
    Gateway-->>Mobile: 201 Created (Mark local event: SYNCED)
    Gateway-->>Manager: Real-time UI update (Delay +17 min highlighted)
```

---

## 4. Planned vs. Actual Calculation Specifications

To eliminate manual delay computations, the system computes five distinct variance metrics:

| Metric | Formula | Trigger Condition |
| :--- | :--- | :--- |
| **Stop Arrival Delay** | $\max(0, T_{\text{actual\_arrival}} - T_{\text{planned\_arrival}})$ | Executed upon `ARRIVED_AT_STOP` event. |
| **Stop Departure Delay** | $\max(0, T_{\text{actual\_departure}} - T_{\text{planned\_departure}})$ | Executed upon `DEPARTED_STOP` event. |
| **Stop Work Duration** | $T_{\text{actual\_departure}} - T_{\text{actual\_arrival}}$ | Calculated when departure is recorded. |
| **Leg Transit Delay** | $(T_{\text{actual\_arrival}}^{(N)} - T_{\text{actual\_departure}}^{(N-1)}) - (T_{\text{planned\_arrival}}^{(N)} - T_{\text{planned\_departure}}^{(N-1)})$ | Calculated between consecutive stops. |
| **Cumulative Trip Delay**| $\sum_{i=1}^{M} \text{StopDelay}_i + \sum_{j=1}^{M-1} \text{TransitDelay}_j$ | Recomputed dynamically on each event. |

---

## 5. Security & Isolation Model

1. **Defense in Depth**: Zero trust between tiers. All API requests require signed asymmetric JWT tokens.
2. **Data Sanitization**: Pydantic v2 enforces strict input validation against SQL injection, XSS payloads, and malformed timestamps.
3. **Audit Trail**: Any update executed by a user with role `MANAGER` or `ADMIN` that modifies operational timestamps requires a mandatory `reason` string and writes to `audit_logs`.
