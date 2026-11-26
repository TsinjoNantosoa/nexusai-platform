# ADR-002: FastAPI modular monolith

Date: 2026-11-25
Status: Accepted for Phase 2

## Decision

Use a Python 3.12 FastAPI modular monolith with SQLAlchemy 2, Alembic, PostgreSQL, Psycopg, Pydantic Settings, Pytest, HTTPX, Ruff, Docker, and Compose. Keep domain modules separate without introducing microservices or an external platform.

## Consequences

Database transactions and row locks are available to wallet services, migrations are explicit, and local infrastructure is reproducible. Shared rate limiting, horizontal scaling, and provider integrations require later decisions.
