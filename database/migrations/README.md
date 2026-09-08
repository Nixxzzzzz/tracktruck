# Database Migrations

Database schema versioning is managed via Alembic in `/backend/alembic`.
To apply migrations:
```bash
cd backend
alembic upgrade head
```
To generate a new migration revision:
```bash
alembic revision --autogenerate -m "description_of_change"
```
Never modify schema tables directly without Alembic revision scripts.
