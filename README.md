# AURELIS FLEET — Luxury Fleet & Logistics Operations Management Platform

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-gold.svg)](#)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16.3-336791.svg)](https://www.postgresql.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2+-black.svg)](https://nextjs.org/)
[![Flutter 3.22](https://img.shields.io/badge/Flutter-3.22-02569B.svg)](https://flutter.dev/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://www.docker.com/)

> **A mission-critical, enterprise-grade operations management system engineered for luxury logistics, industrial supply chains, and high-precision transport tracking.**

---

## 💎 Executive Overview

**AURELIS FLEET** bridges the gap between executive dispatch oversight and rugged field operations. Moving beyond simplistic vehicle trackers, the platform anchors its entire business domain around the **Composite Operational Unit**:

$$\mathbf{Operational\ Unit} = \text{Vehicle} + \text{Driver} + \text{Trip} + \text{Material} + \text{Route} + \text{Stops} + \text{Events} + \text{Audit}$$

### Key Value Pillars

| Pillar | Capability | Operational Impact |
| :--- | :--- | :--- |
| **Planned vs. Actual Engine** | Automated arrival/departure timestamp variance calculation at every multi-stop milestone. | Eliminates human estimation; instantly reveals route delays with exact minutes. |
| **Immutable Event Sourcing** | Append-only event store (`trip_events`) capturing field actions without silent overwrites. | 100% auditable timeline from gate departure to final depot return. |
| **Offline-First Field Terminal** | Local SQLite event buffering with deterministic idempotency keys and auto-sync. | Zero data loss in cellular dead zones across national highways and remote plants. |
| **Manager Correction Audit** | Role-gated manual adjustments that require justification and preserve historical states. | Complete accountability for route alterations, supervisor overrides, and manual times. |
| **Luxury Automotive UI** | Dark graphite instrumentation theme with champagne gold accents and tactile touchpoints. | High-contrast ergonomics for drivers; executive telemetry control center for managers. |

---

## 🏛️ System Architecture

```mermaid
flowchart TB
    subgraph Clients["1. Presentation Tier"]
        Web["Web Command Center\n(Next.js 14 App Router / React / TypeScript)"]
        Mobile["Android Driver Terminal\n(Flutter 3.22 / Dart / Drift SQLite)"]
    end

    subgraph Security["2. Gateway & Security Boundary"]
        Proxy["Nginx Reverse Proxy / SSL Termination"]
        AuthMid["JWT Auth & Server-Side RBAC Enforcement"]
        RateLimit["Redis-Powered Rate Limiter & Idempotency Filter"]
    end

    subgraph Core["3. Backend Application Core (FastAPI / Python 3.12)"]
        TripStateMachine["Trip State Machine & Invariant Engine"]
        VarianceCalc["Planned vs. Actual Delay Calculator"]
        EventStore["Append-Only Event Sourcing Service"]
        SyncManager["Offline Sync & Conflict Resolution Engine"]
        AuditService["Operational Audit Trail Service"]
    end

    subgraph Storage["4. Persistence & Cache Tier"]
        Postgres[(PostgreSQL 16 Enterprise Relational DB)]
        Redis[(Redis 7 - Token Blacklist & Locks)]
        S3[(MinIO / S3 Object Store - Proofs & Docs)]
    end

    Web -->|HTTPS / REST| Proxy
    Mobile -->|HTTPS / REST / Idempotent Sync| Proxy
    Proxy --> AuthMid
    AuthMid --> RateLimit
    RateLimit --> Core

    Core --> Postgres
    Core --> Redis
    Core --> S3
```

---

## 🎨 Visual Identity & Luxury Design System

The platform adopts a disciplined, high-end automotive instrumentation theme designed for maximum legibility and executive authority.

```
Background:         #0B0C0E   (Deep Graphite)
Primary Surface:    #111316   (Charcoal Surface)
Secondary Surface:  #17191D   (Elevated Card Surface)
Luxury Accent:      #C8A96B   (Champagne Gold)
Border Subtle:      #2A2D32   (Metallic Titanium)
Primary Text:       #F4F1EA   (Off-White High Contrast)
Secondary Text:     #A7A8AA   (Muted Platinum)
Success State:      #4E9F76   (Muted Forest Emerald)
Warning State:      #D4A359   (Warm Amber)
Danger State:       #C75D5D   (Restrained Crimson)
```

---

## 🔄 Trip State Machine & Lifecycle

Every trip follows a strictly verified sequence of states enforced by database constraints and service-layer invariants:

```mermaid
stateDiagram-v2
    [*] --> PLANNED: Created by Dispatcher
    PLANNED --> ASSIGNED: Vehicle & Driver Allocated
    ASSIGNED --> READY: Pre-trip Checks Passed
    READY --> STARTED: Driver initiates Trip (Actual Start recorded)
    
    state "Multi-Stop Transit Loop" as Loop {
        [*] --> IN_TRANSIT
        IN_TRANSIT --> ARRIVED: Driver taps ARRIVED
        ARRIVED --> LOADING_UNLOADING: Loading/Unloading starts
        LOADING_UNLOADING --> READY_TO_DEPART: Manifest verified
        READY_TO_DEPART --> DEPARTED: Driver taps DEPARTED
        DEPARTED --> IN_TRANSIT: Next stop queued
    }

    Loop --> RETURNING: Final Stop Departed
    RETURNING --> RETURNED: Arrived at Home Depot
    RETURNED --> COMPLETED: Post-trip Reconciliation Verified
    
    Loop --> DELAYED: Variance > Threshold
    DELAYED --> Loop: Resumed
    
    Loop --> BREAKDOWN: Vehicle Incident
    BREAKDOWN --> Loop: Roadside Assistance / Resume
    
    PLANNED --> CANCELLED: Dispatch Cancellation
    ASSIGNED --> CANCELLED: Dispatch Cancellation
    COMPLETED --> [*]
    CANCELLED --> [*]
```

---

## 👥 Role-Based Access Control (RBAC)

Authorization is verified strictly on the backend API layer:

| Resource / Capability | SUPER_ADMIN | ADMIN | MANAGER | SUPERVISOR | DRIVER |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **System Settings & User Provisioning** | Full | Full | None | None | None |
| **System-Wide Audit Logs** | Read All | Read All | Scoped | None | None |
| **Master Data (Vehicles, Drivers, Hubs)** | Full CRUD | Full CRUD | View / Edit | Read Only | None |
| **Trip Planning & Template Dispatch** | Full | Full | Full | None | None |
| **Manual Operational Overrides** | Full (Audited) | Full (Audited) | Full (Audited) | None | None |
| **Operations Control Center** | View All | View All | View All | Assigned Depot | None |
| **Field Execution (Arrive/Depart)** | Override | Override | Override | Depot Level | Assigned Trip |
| **Incident & Delay Logging** | Full | Full | Full | Full | Assigned Trip |
| **Mobile Application Access** | Blocked | Blocked | Blocked | Blocked | Primary Client |

---

## 🗄️ Database Architecture Highlights

```mermaid
erDiagram
    USERS ||--o{ AUDIT_LOGS : generates
    ROLES ||--o{ USERS : classifies
    VEHICLES ||--o{ TRIPS : deployed_in
    DRIVERS ||--o{ TRIPS : operates
    LOCATIONS ||--o{ TRIP_STOPS : situated_at
    MATERIALS ||--o{ TRIP_MATERIALS : manifests
    ROUTE_TEMPLATES ||--o{ TRIPS : blueprints
    TRIPS ||--|{ TRIP_STOPS : sequences
    TRIPS ||--|{ TRIP_MATERIALS : carries
    TRIPS ||--o{ TRIP_EVENTS : chronicles
    TRIPS ||--o{ INCIDENTS : records
```

Comprehensive relational models, migration definitions, and field dictionaries are detailed in [`/docs/database.md`](docs/database.md).

---

## 📂 Repository Structure

```
tracktruck/
├── apps/
│   ├── web/                     # Next.js 14 Luxury Operations Dashboard
│   └── mobile/                  # Flutter Android Driver Field Application
├── backend/
│   ├── app/
│   │   ├── core/                # Config, Database Session, Security, Exceptions
│   │   ├── models/              # SQLAlchemy 2.0 Declarative ORM Models
│   │   ├── schemas/             # Pydantic v2 Request/Response Schemas
│   │   ├── services/            # State Machine, Event Sourcing, Variance Engine
│   │   └── api/v1/              # Versioned REST API Controllers
│   ├── alembic/                 # Database Migration Revisions
│   └── tests/                   # Pytest Test Suite
├── database/                    # SQL seed fixtures, schema dumps
├── docs/                        # Complete Engineering Documentation Suite
│   ├── architecture.md          # Multi-tier System Architecture & Topology
│   ├── database.md              # Complete ERD & Relational Data Dictionary
│   ├── trip-lifecycle.md        # State Machine Transitions & Invariants
│   ├── api.md                   # REST Endpoints & Idempotency Specifications
│   ├── authentication.md        # JWT Token Lifecycle & Security Hardening
│   ├── permissions.md           # Granular RBAC Permissions Matrix
│   ├── mobile.md                # Offline-First Drift SQLite Sync Architecture
│   ├── deployment.md            # Docker, Production Tuning & Monitoring
│   └── decisions/               # Architecture Decision Records (ADR 001 - 002)
├── infrastructure/              # Nginx reverse proxy & environment configs
└── docker-compose.yml           # Unified orchestration (FastAPI, Postgres, Redis)
```

---

## 🚀 Rapid Local Setup (Quickstart)

### 1. Prerequisites
- Docker Engine 24+ & Docker Compose v2+
- Python 3.12+
- Node.js 20+ & pnpm / npm
- Flutter SDK 3.22+ (for mobile development)

### 2. Launch Local Infrastructure
```bash
# Clone the repository
git clone https://github.com/Nixxzzzzz/tracktruck.git
cd tracktruck

# Launch PostgreSQL 16, Redis 7, and Backend API
docker compose up -d
```

### 3. Initialize Database Migrations & Seeds
```bash
# Run database migrations
docker compose exec backend alembic upgrade head

# Load master data seeds (Vehicles, Drivers, Route Templates, Test Accounts)
docker compose exec backend python -m app.core.seed
```

### 4. Access Services
- **Web Operations Console**: `http://localhost:3000`
- **Backend Interactive Swagger API**: `http://localhost:8000/docs`
- **PostgreSQL Database**: `localhost:5432` (Database: `aurelis_fleet`)

---

## 📖 Complete Documentation Index

For complete technical specifications, please consult the dedicated documentation modules:
- [System Architecture](docs/architecture.md)
- [Database Schema & ERD](docs/database.md)
- [Trip Lifecycle & State Machine](docs/trip-lifecycle.md)
- [API Specification & Contracts](docs/api.md)
- [Authentication & Security Model](docs/authentication.md)
- [Role-Based Access Control (RBAC)](docs/permissions.md)
- [Mobile Offline Sync Engine](docs/mobile.md)
- [Deployment & DevOps Strategy](docs/deployment.md)
- [Architecture Decision Records (ADRs)](docs/decisions/)
