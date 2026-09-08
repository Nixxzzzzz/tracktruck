# AURELIS FLEET — Architecture & Engineering Documentation Suite

Welcome to the technical documentation directory for the **AURELIS FLEET** platform.

This directory serves as the definitive engineering manual for architects, full-stack engineers, mobile developers, QA engineers, and DevOps operators.

---

## 📚 Documentation Navigation Directory

| Document | Purpose | Key Contents |
| :--- | :--- | :--- |
| **[Architecture Overview](architecture.md)** | Multi-tier system design & platform topology | Client tier, API boundary, backend modularization, telemetry engine, caching & storage. |
| **[Database Architecture](database.md)** | Relational model, ERD & data dictionary | PostgreSQL 16 schema, entity relationships, immutable events vs. mutable operational records, indexing strategy. |
| **[Trip Lifecycle & State Machine](trip-lifecycle.md)** | State transitions & operational invariants | Valid state transitions, stop progression rules, variance calculations, breakdown and hold workflows. |
| **[API Specification](api.md)** | REST contracts & integration standards | Response envelopes, error codes, versioning, idempotency keys, core operational endpoints. |
| **[Authentication & Security](authentication.md)** | Auth engine, token lifecycle & security | JWT token rotation, bcrypt password hashing, rate limiting, audit trail logging. |
| **[Permissions & RBAC](permissions.md)** | Role-based access control matrix | Granular permission capabilities across SUPER_ADMIN, ADMIN, MANAGER, SUPERVISOR, and DRIVER. |
| **[Mobile & Offline Strategy](mobile.md)** | Android driver client & offline sync | Drift SQLite database, event buffering, sync queue state machine, idempotency and clock skew handling. |
| **[Deployment & DevOps](deployment.md)** | Infrastructure, containerization & CI/CD | Docker Compose orchestration, PostgreSQL tuning, environment variables, healthchecks and backup runbooks. |
| **[Architecture Decisions (ADRs)](decisions/)** | Architectural Decision Records | Formal records documenting key architectural choices, trade-offs, and design rationale. |

---

## 🏛️ Platform Core Principles

1. **Immutable Historical Events**: Operational timelines are append-only. No status change, arrival timestamp, or manager correction ever replaces past event entries.
2. **Deterministic Offline Sync**: Mobile drivers can record critical operational milestones in areas with zero cellular reception without risk of duplicate creation or event loss.
3. **Planned vs. Actual as First-Class Entities**: Every transit milestone records both planned and actual values, automatically deriving variances, stop durations, and fleet delays.
4. **Zero-Trust Server Authorization**: Role validation and business rules are strictly verified on the API layer. Client-side UI state is never assumed to be authoritative.
