# Role-Based Access Control (RBAC) & Permissions

## 1. Role Taxonomy

AURELIS FLEET defines five non-overlapping roles structured hierarchically by operational scope:

```
SUPER_ADMIN (System & Master Authority)
   └── ADMIN (Operational Director)
         ├── MANAGER (Fleet Operations Dispatcher)
         │     └── SUPERVISOR (Depot / Field Overseer)
         └── DRIVER (Tactical Field Operator)
```

---

## 2. Comprehensive Resource Capability Matrix

| Operational Capability | SUPER_ADMIN | ADMIN | MANAGER | SUPERVISOR | DRIVER |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **System & User Configuration** | | | | | |
| Manage System Settings & Parameters | ✅ | ❌ | ❌ | ❌ | ❌ |
| Create / Deactivate User Accounts | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Global Audit Log Stream | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Master Data Management** | | | | | |
| Create / Edit Vehicles & Documents | ✅ | ✅ | 👁️ (Read Only) | 👁️ (Read Only) | ❌ |
| Create / Edit Driver Profiles | ✅ | ✅ | 👁️ (Read Only) | 👁️ (Read Only) | ❌ |
| Create / Edit Locations & Hubs | ✅ | ✅ | ✅ | 👁️ (Read Only) | ❌ |
| Create / Edit Cargo Materials | ✅ | ✅ | ✅ | 👁️ (Read Only) | ❌ |
| Create / Edit Route Templates | ✅ | ✅ | ✅ | 👁️ (Read Only) | ❌ |
| **Trip Planning & Execution** | | | | | |
| Plan & Dispatch New Trips | ✅ | ✅ | ✅ | ❌ | ❌ |
| Cancel Unstarted Planned Trips | ✅ | ✅ | ✅ | ❌ | ❌ |
| Modify Planned Route Waypoints | ✅ | ✅ | ✅ | ❌ | ❌ |
| Perform Audited Manual Corrections | ✅ | ✅ | ✅ | ❌ | ❌ |
| Record Depot Gate Check-in | ✅ | ✅ | ✅ | ✅ | ❌ |
| Record Transit Stop Actions (Arrive/Depart)| ⚠️ Override | ⚠️ Override | ⚠️ Override | ⚠️ Override | ✅ (Assigned) |
| **Exceptions & Incidents** | | | | | |
| Report Field Incidents / Delays | ✅ | ✅ | ✅ | ✅ | ✅ (Assigned) |
| Resolve Incidents & Clear Holds | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Operations Dashboards & Reports** | | | | | |
| View Live Operations Telemetry | ✅ | ✅ | ✅ | ✅ (Assigned Hub)| ❌ |
| Generate Delay & Utilization Analytics | ✅ | ✅ | ✅ | ❌ | ❌ |
| Access Mobile Driver Terminal | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 3. Server-Side Enforcement Pattern

Permissions are strictly validated at the FastAPI route boundary via Python dependency injection. Client-side hiding of UI elements is purely ergonomic and never trusted for security:

```python
# FastAPI Permission Guard Example
from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user
from app.models.user import User

def require_roles(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role_id not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

# Usage on protected endpoints:
# @router.post("/trips", dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "MANAGER"))])
```
