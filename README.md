# NexusAI

NexusAI is a French/English AI-character chat demonstration. The repository contains a portable React/Vite SPA and a Phase 2 FastAPI modular monolith foundation for real identity, sessions, PostgreSQL persistence, server-authoritative products, and a transactional gem wallet.

## Current status

- Phase 1.1 frontend stabilization is merged in the local `origin/main` baseline.
- Phase 2 implements registration, login, logout, current-user sessions, CSRF bootstrap, roles, wallet ledger primitives, products, migrations, health checks, and local Docker infrastructure.
- Stripe Checkout, Customer Portal, signed webhooks, AI provider calls, conversations, moderation workflows, and production deployment remain later phases.

## Local startup

Requirements: Python 3.12, Docker Compose, Bun, and an available Docker daemon.

```powershell
docker compose up -d --build
cd frontend
bun install --frozen-lockfile
$env:VITE_DATA_MODE = "api"
bun run dev
```

The frontend runs at `http://localhost:5173`; the backend runs at `http://localhost:8000`. Compose uses PostgreSQL on `127.0.0.1:55432` and a project-specific volume/network. It does not touch another PostgreSQL service.

The backend container runs `alembic upgrade head` and the idempotent product seed at startup. The explicit procedure is:

```powershell
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.seed
```

Integration tests use a separate disposable PostgreSQL service. They fail closed when the explicit test configuration is missing and never fall back to the development database:

```powershell
docker compose --profile test up -d postgres-test
Set-Location backend
$env:NEXUSAI_TEST_DATABASE_URL = "postgresql+psycopg://<test-role>:<test-password>@127.0.0.1:55433/nexusai_test"
$env:NEXUSAI_TEST_DATABASE_NAME = "nexusai_test"
$env:NEXUSAI_TEST_DATABASE_ROLE = "<test-role>"
$env:NEXUSAI_TEST_DATABASE_DISPOSABLE = "true"
$env:NEXUSAI_DEVELOPMENT_DATABASE_URL = "postgresql+psycopg://<dev-role>:<dev-password>@127.0.0.1:55432/nexusai"
python -m pytest tests -q
```

Only the disposable test service may be used for destructive fixture cleanup or Alembic downgrade validation. See `docs/operations/DATABASE_BACKUP_RESTORE.md` before any recovery operation.

Provisioning an administrator is explicit and requires an existing fictional local account:

```powershell
docker compose exec backend python -m app.auth.provision_admin --email admin@example.test
```

## Validation

Backend local environment and tests are documented in `docs/audit/PHASE_2_1_TEST_REPORT.md`. The PostgreSQL integration suite requires an isolated `nexusai_test` database and never uses SQLite as evidence for locking behavior. Frontend validation remains Bun-first.

For a production-shaped configuration, set `NEXUSAI_ENVIRONMENT=production`, `NEXUSAI_COOKIE_SECURE=true`, explicit HTTPS `NEXUSAI_ALLOWED_ORIGINS`, and explicit `NEXUSAI_TRUSTED_HOSTS`. Startup rejects unsafe production values; this does not claim TLS, CSP, distributed rate limiting, or production deployment readiness.

## Boundaries

Use `VITE_DATA_MODE=mock` for the independent in-memory demonstration. Use `VITE_DATA_MODE=api` only with the FastAPI service. No production credentials or real payment credentials belong in this repository.
