# REST API Specification & Service Contracts (Validated & Enhanced)

## 1. Architectural Principles & Standards

1. **Protocol**: HTTPS / REST over JSON.
2. **Standard Base URL**: `/api/v1`
3. **Authentication**: Bearer JWT token in HTTP Authorization Header:
   `Authorization: Bearer <access_token>`
4. **Idempotency**: All state-mutating requests (`POST`, `PUT`, `PATCH`) support an `Idempotency-Key` header (UUID v4) to prevent duplicate processing on mobile retries.
5. **Server-Side Enforcement**: All business rules, status transition validations, and role permissions are enforced server-side inside transactional service boundaries. Client UI never decides validity.

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
| `POST` | `/api/v1/auth/logout` | Invalidate active session & revoke refresh token in Redis. | Authenticated |
| `GET` | `/api/v1/auth/me` | Fetch active user profile, permissions, and roles. | Authenticated |

### 3.2 Master Registries (Soft-Delete & Archive Protected)
| Method | Endpoint | Description | Permitted Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/vehicles` | Filtered list of fleet vehicles (status, type, search). | ALL |
| `POST` | `/api/v1/vehicles` | Register new fleet vehicle. | SUPER_ADMIN, ADMIN |
| `GET` | `/api/v1/vehicles/{id}` | Detailed vehicle profile, document status, and trip history. | ALL |
| `PATCH` | `/api/v1/vehicles/{id}` | Update vehicle specifications or active status. | SUPER_ADMIN, ADMIN |
| `DELETE`| `/api/v1/vehicles/{id}` | Soft-delete/archive vehicle (preserves historical trips). | SUPER_ADMIN, ADMIN |
| `GET` | `/api/v1/drivers` | Directory of commercial drivers with license validity. | ALL |
| `POST` | `/api/v1/drivers` | Register driver profile. | SUPER_ADMIN, ADMIN |
| `GET` | `/api/v1/drivers/{id}` | Driver profile, license expiry, and trip log. | ALL |
| `DELETE`| `/api/v1/drivers/{id}` | Soft-delete/archive driver (preserves historical trips). | SUPER_ADMIN, ADMIN |
| `GET` | `/api/v1/locations` | List operational locations (plants, depots, warehouses). | ALL |
| `POST` | `/api/v1/locations` | Register new operational location. | SUPER_ADMIN, ADMIN, MANAGER |
| `GET` | `/api/v1/materials` | Cargo catalogue with standard units and weights. | ALL |
| `POST` | `/api/v1/materials` | Register new cargo material. | SUPER_ADMIN, ADMIN, MANAGER |
| `GET` | `/api/v1/route-templates`| Directory of reusable multi-stop route blueprints. | ALL |
| `POST` | `/api/v1/route-templates`| Create multi-stop template with sequenced waypoints. | SUPER_ADMIN, ADMIN, MANAGER |

### 3.3 Trip Planning & Dispatch Engine
| Method | Endpoint | Description | Permitted Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/trips` | Query trips by date range, vehicle, driver, status, delay. | ALL |
| `POST` | `/api/v1/trips` | Schedule and dispatch new trip (stops, cargo manifest). | SUPER_ADMIN, ADMIN, MANAGER |
| `GET` | `/api/v1/trips/{id}` | Complete trip ledger: route, planned vs. actual, timeline. | ALL |
| `PATCH` | `/api/v1/trips/{id}` | Modify planned parameters before trip has started. | SUPER_ADMIN, ADMIN, MANAGER |
| `POST` | `/api/v1/trips/{id}/cancel` | Cancel unstarted or assigned trip with mandatory reason. | SUPER_ADMIN, ADMIN, MANAGER |

### 3.4 Driver Operational Endpoints (Mobile Optimized)
| Method | Endpoint | Description | Permitted Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/driver/today-trip` | Fetch current active trip assigned to logged-in driver. | DRIVER |
| `POST` | `/api/v1/trips/{id}/events` | Record single operational milestone (arrived, departed). | DRIVER, SUPERVISOR, MANAGER |
| `POST` | `/api/v1/trips/events/sync` | Batch sync offline events queued by mobile client. | DRIVER |
| `POST` | `/api/v1/trips/{id}/delays` | Report manual delay with category, minutes, and reason. | DRIVER, SUPERVISOR, MANAGER |
| `POST` | `/api/v1/trips/{id}/incidents` | Report breakdown, accident, puncture or emergency. | DRIVER, SUPERVISOR, MANAGER |

### 3.5 Manager Operational Overrides & Exceptions
| Method | Endpoint | Description | Permitted Roles |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/trips/{id}/manual-correction` | Audited manager operational adjustment (modifies actuals + logs audit). | SUPER_ADMIN, ADMIN, MANAGER |
| `GET` | `/api/v1/incidents` | Filtered list of operational incidents (severity, resolved). | ALL |
| `PATCH` | `/api/v1/incidents/{id}/resolve`| Mark incident resolved with action details and downtime. | SUPERVISOR, MANAGER, ADMIN |

### 3.6 Telemetry Dashboards & Analytical Reporting
| Method | Endpoint | Description | Permitted Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/operations/summary` | Real-time counts: Active vehicles, delayed trips, incidents. | SUPER_ADMIN, ADMIN, MANAGER, SUPERVISOR |
| `GET` | `/api/v1/operations/live-board` | Active trip cards with delay counters and current stop. | SUPER_ADMIN, ADMIN, MANAGER, SUPERVISOR |
| `GET` | `/api/v1/reports/daily-operations` | Date-filtered variance report (planned vs actual). | SUPER_ADMIN, ADMIN, MANAGER |
| `GET` | `/api/v1/reports/delay-analysis` | Aggregated delay breakdown by category and route. | SUPER_ADMIN, ADMIN, MANAGER |
| `GET` | `/api/v1/reports/vehicle-utilization`| Vehicle active hours, distance, and trip completion rates. | SUPER_ADMIN, ADMIN, MANAGER |
| `GET` | `/api/v1/reports/driver-performance`| Driver punctuality, on-time percentage, and logged incidents. | SUPER_ADMIN, ADMIN, MANAGER |
| `GET` | `/api/v1/audit-logs` | Immutable audit log trail with filter by user and entity. | SUPER_ADMIN, ADMIN |

---

## 4. Contract Details for Key Operations

### 4.1 Reporting a Manual Delay (`POST /api/v1/trips/{id}/delays`)
```json
{
  "stop_id": "f4a0d3e6-3c7d-4b5e-ab02-b5ae604daf04",
  "delay_type": "TRAFFIC",
  "delay_minutes": 25,
  "reason": "Major highway congestion before toll plaza",
  "notes": "Traffic police redirecting heavy vehicles through bypass"
}
```

### 4.2 Reporting an Incident (`POST /api/v1/trips/{id}/incidents`)
```json
{
  "stop_id": "a5b1e4f7-4d8e-4c6f-bc13-c6bf715eb005",
  "incident_type": "ENGINE_PROBLEM",
  "severity": "HIGH",
  "description": "Coolant temperature alarm triggered; engine overheating",
  "location_name": "NH46 near Dewas Bypass, KM 142",
  "latitude": 22.9676,
  "longitude": 76.0534,
  "delay_caused_minutes": 45
}
```
