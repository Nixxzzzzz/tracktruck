# Infrastructure, Deployment & DevOps Specification

## 1. Containerization & Service Orchestration

AURELIS FLEET provides containerized configurations for development, staging, and production environments via Docker and Docker Compose.

```mermaid
flowchart TD
    subgraph Host["Docker Production Host"]
        ReverseProxy["Nginx Ingress (Ports 80 / 443)\nTLS Termination & Static Asset Caching"]
        
        subgraph AppServices["Application Containers"]
            WebContainer["Next.js 14 Web Frontend\n(Port 3000)"]
            BackendContainer["FastAPI Core Engine\n(Port 8000, 4 Uvicorn Workers)"]
        end

        subgraph DataTier["Data Services"]
            PostgresContainer[("PostgreSQL 16\nPersistent Volume")]
            RedisContainer[("Redis 7 In-Memory Store\nPersistent AOF")]
            MinIOContainer[("MinIO S3-Compatible Store\nPersistent Volume")]
        end
    end

    ReverseProxy -->|/| WebContainer
    ReverseProxy -->|/api| BackendContainer
    BackendContainer --> PostgresContainer
    BackendContainer --> RedisContainer
    BackendContainer --> MinIOContainer
```

---

## 2. Production Docker Compose Template (`infrastructure/docker-compose.prod.yml`)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: aurelis_postgres
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-aurelis_fleet}
      POSTGRES_USER: ${POSTGRES_USER:-aurelis_admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Database password required}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    command: >
      postgres -c max_connections=200
               -c shared_buffers=1GB
               -c effective_cache_size=3GB
               -c maintenance_work_mem=256MB
               -c checkpoint_completion_target=0.9
               -c wal_buffers=16MB
               -c default_statistics_target=100
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: aurelis_redis
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:?Redis password required}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: aurelis_backend
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:?JWT Secret required}
      ENVIRONMENT: production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 15s
      timeout: 5s
      retries: 3

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    container_name: aurelis_web
    restart: always
    depends_on:
      - backend
    environment:
      NEXT_PUBLIC_API_BASE_URL: https://fleet.aurelis.io/api/v1

volumes:
  postgres_data:
  redis_data:
```

---

## 3. Database Backup & Disaster Recovery Runbook

1. **Automated Nightly Full Backup**:
   ```bash
   # Executed via daily systemd cron at 02:00 UTC
   docker exec -t aurelis_postgres pg_dump -U aurelis_admin -F c aurelis_fleet > /backups/aurelis_fleet_$(date +%Y%m%d_%H%M%S).dump
   ```
2. **Offsite Synchronization**:
   Backups are encrypted via GPG (`AES-256`) and synchronized to an isolated cold-storage S3 bucket with 30-day retention policies.
3. **Restoration Drill**:
   ```bash
   pg_restore -U aurelis_admin -d aurelis_fleet_recovery --clean /backups/aurelis_fleet_20260908.dump
   ```

---

## 4. Monitoring & Observability

- **Structured JSON Logging**: All application logs emit structured JSON with correlation IDs (`request_id`, `user_id`, `trip_id`).
- **Health Checks**:
  - `/api/v1/health` (Liveness check, returns 200).
  - `/api/v1/health/ready` (Readiness check verifying PostgreSQL connection pool and Redis ping).
