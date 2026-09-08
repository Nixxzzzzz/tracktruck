"""
==============================================================================
AURELIS FLEET — Development Only Seed Data
==============================================================================
WARNING: This script is intended strictly for local development and testing.
DO NOT execute this script in staging or production environments.
==============================================================================
"""

import sys
import os

# Base roles defined in Phase 0 RBAC
DEV_ROLES = [
    {"role_id": "SUPER_ADMIN", "description": "System owner with unrestricted administrative access"},
    {"role_id": "ADMIN", "description": "Operations director with fleet-wide management scope"},
    {"role_id": "MANAGER", "description": "Fleet operations dispatcher creating and managing trips"},
    {"role_id": "SUPERVISOR", "description": "Depot and field supervisor overseeing terminal operations"},
    {"role_id": "DRIVER", "description": "Field transport driver operating vehicles and recording milestones"},
]

# Development-only user credentials (PASSWORDS ARE FOR LOCAL DEV TESTING ONLY)
DEV_USERS = [
    {
        "username": "dev.admin",
        "email": "dev.admin@aurelis.local",
        "password": "DevPassword123!",
        "full_name": "Development Super Admin",
        "role_id": "SUPER_ADMIN",
    },
    {
        "username": "dev.manager",
        "email": "dev.manager@aurelis.local",
        "password": "DevPassword123!",
        "full_name": "Development Fleet Manager",
        "role_id": "MANAGER",
    },
    {
        "username": "dev.supervisor",
        "email": "dev.supervisor@aurelis.local",
        "password": "DevPassword123!",
        "full_name": "Development Depot Supervisor",
        "role_id": "SUPERVISOR",
    },
    {
        "username": "dev.driver",
        "email": "dev.driver@aurelis.local",
        "password": "DevPassword123!",
        "full_name": "Ramesh Kumar (Dev Driver)",
        "role_id": "DRIVER",
    },
]

if __name__ == "__main__":
    print("[DEV SEED] This module defines development-only seed fixtures.")
    print(f"[DEV SEED] Defined {len(DEV_ROLES)} system roles and {len(DEV_USERS)} development test accounts.")
