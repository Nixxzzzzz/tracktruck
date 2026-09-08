# REST API Specification & Service Contracts

## 1. Architectural Principles & Standards

1. **Protocol**: HTTPS / REST over JSON.
2. **Standard Base URL**: `/api/v1`
3. **Authentication**: Bearer JWT token in HTTP Authorization Header:
   `Authorization: Bearer <access_token>`
4. **Idempotency**: All state-mutating requests (`POST`, `PUT`, `PATCH`) support an `Idempotency-Key` header (UUID v4) to prevent duplicate processing on mobile retries.

---

## 2. Standard Response Envelopes

### 2.1 Success Envelope
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "timestamp": "2026-09-08T18:15:00Z",
    "request_id": "req-9b1deb4d-3b7d"
  }
}
```

### 2.2 Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "Stop #2 cannot be marked as ARRIVED before Stop #1 has DEPARTED.",
    "details": {
      "trip_id": "8a31e8c1-5bf3-4632-a63b-6e7a27d14201",
      "attempted_state": "ARRIVED",
      "required_prior_state": "DEPARTED"
    }
  },
  "timestamp": "2026-09-08T18:15:00Z"
}
```

---

## 3. Core Endpoint Catalog

### 3.1 Authentication & Profile
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/auth/login` | Authenticate credentials & issue access/refresh tokens. | Public |
| `POST` | `/api/v1/auth/refresh` | Exchange refresh token for new access JWT. | Public |
| `POST` | `/api/v1/auth/logout` | Invalidate active session & revoke refresh token. | Authenticated |
| `GET` | `/api/v1/auth/me` | Fetch active user profile, permissions, and roles. | Authenticated |

### 3.2 Master Registries
| Method | Endpoint | Description | Permitted Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/vehicles` | Filtered list of fleet vehicles (status, type, search). | ALL |
| `POST` | `/api/v1/vehicles` | Register new fleet vehicle. | SUPER_ADMIN, ADMIN |
| `GET` | `/api/v1/vehicles/{id}` | Detailed vehicle profile, document status, and trip history. | ALL |
| `PATCH` | `/api/v1/vehicles/{id}` | Update vehicle specifications or active status. | SUPER_ADMIN, ADMIN |
| `GET` | `/api/v1/drivers` | Directory of commercial drivers with license validity. | ALL |
| `POST` | `/api/v1/drivers` | Register driver profile. | SUPER_ADMIN, ADMIN |
| `GET` | `/api/v1/locations` | List operational locations (plants, depots, warehouses). | ALL |
| `POST` | `/api/v1/locations` | Register new operational location. | SUPER_ADMIN, ADMIN, MANAGER |
| `GET` | `/api/v1/materials` | Cargo catalogue with standard units and weights. | ALL |
| `GET` | `/api/v1/route-templates`| Directory of reusable multi-stop route blueprints. | ALL |
| `POST` | `/api/v1/route-templates`| Create multi-stop template with sequenced waypoints. | SUPER_ADMIN, ADMIN, MANAGER |

### 3.3 Trip Operations Engine
| Method | Endpoint | Description | Permitted Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/trips` | Query trips by date, vehicle, driver, status, delay. | ALL |
| `POST` | `/api/v1/trips` | Schedule and dispatch new trip (stops, cargo manifest). | SUPER_ADMIN, ADMIN, MANAGER |
| `GET` | `/api/v1/trips/{id}` | Complete trip ledger: route, planned vs. actual, timeline. | ALL |
| `PATCH` | `/api/v1/trips/{id}` | Modify planned parameters before trip has started. | SUPER_ADMIN, ADMIN, MANAGER |
| `POST` | `/api/v1/trips/{id}/events` | Record single operational milestone (arrived, departed). | DRIVER, SUPERVISOR, MANAGER |
| `POST` | `/api/v1/trips/events/sync` | Batch sync offline events queued by mobile client. | DRIVER |
| `POST` | `/api/v1/trips/{id}/manual-correction` | Audited manager operational adjustment. | SUPER_ADMIN, ADMIN, MANAGER |
| `POST` | `/api/v1/trips/{id}/incidents` | Report breakdown, accident, puncture or delay event. | DRIVER, SUPERVISOR, MANAGER |
| `PATCH` | `/api/v1/incidents/{id}/resolve`| Mark incident resolved with action details. | SUPERVISOR, MANAGER, ADMIN |

### 3.4 Operational Dashboards & Reporting
| Method | Endpoint | Description | Permitted Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/operations/summary` | Real-time counts: Active vehicles, delayed trips, incidents. | SUPER_ADMIN, ADMIN, MANAGER, SUPERVISOR |
| `GET` | `/api/v1/operations/live-board` | Active trip cards with delay counters and current stop. | SUPER_ADMIN, ADMIN, MANAGER, SUPERVISOR |
| `GET` | `/api/v1/reports/daily-operations` | Date-filtered variance report (planned vs actual). | SUPER_ADMIN, ADMIN, MANAGER |
| `GET` | `/api/v1/reports/delay-analysis` | Aggregated delay breakdown by category and route. | SUPER_ADMIN, ADMIN, MANAGER |
| `GET` | `/api/v1/audit-logs` | Immutable audit log trail with filter by user and entity. | SUPER_ADMIN, ADMIN |

---

## 4. Contract Details for Key Operations

### 4.1 Create Trip (`POST /api/v1/trips`)
```json
{
  "trip_date": "2026-09-09",
  "vehicle_id": "c1f7a0b3-9e4a-4e2b-98df-82db371a7d01",
  "driver_id": "d2e8b1c4-1a5b-4f3c-89e0-93ec482b8e02",
  "origin_location_id": "e3f9c2d5-2b6c-4a4d-9af1-a4fd593c9f03",
  "destination_location_id": "e3f9c2d5-2b6c-4a4d-9af1-a4fd593c9f03",
  "trip_type": "ROUND_TRIP",
  "priority": "HIGH",
  "planned_start_time": "2026-09-09T06:00:00Z",
  "planned_return_time": "2026-09-09T18:00:00Z",
  "notes": "Fragile building supplies delivery",
  "stops": [
    {
      "sequence_number": 1,
      "location_id": "f4a0d3e6-3c7d-4b5e-ab02-b5ae604daf04",
      "planned_arrival": "2026-09-09T08:30:00Z",
      "planned_departure": "2026-09-09T09:30:00Z",
      "loading_required": false,
      "unloading_required": true,
      "notes": "Unload 50 bags cement at Bay 3"
    },
    {
      "sequence_number": 2,
      "location_id": "a5b1e4f7-4d8e-4c6f-bc13-c6bf715eb005",
      "planned_arrival": "2026-09-09T11:00:00Z",
      "planned_departure": "2026-09-09T12:00:00Z",
      "loading_required": false,
      "unloading_required": true,
      "notes": "Unload remaining 50 bags"
    }
  ],
  "materials": [
    {
      "material_id": "b6c2f5a8-5e9f-4d7a-cd24-d7cf826fc106",
      "quantity": 100,
      "weight_tons": 5.0,
      "notes": "Portland Pozzolana Cement"
    }
  ]
}
```

### 4.2 Manager Operational Correction (`POST /api/v1/trips/{id}/manual-correction`)
```json
{
  "entity_type": "trip_stops",
  "entity_id": "f4a0d3e6-3c7d-4b5e-ab02-b5ae604daf04",
  "field_name": "actual_departure",
  "new_value": "2026-09-09T09:42:00Z",
  "reason": "Driver reported cellular dead-zone at plant exit gate. Verified with gate security ledger."
}
```
Response will return the adjusted stop, recalculated delay metrics, and confirmed `audit_log_id`.
