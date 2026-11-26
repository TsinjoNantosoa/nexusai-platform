# NexusAI project rules

## Scope

NexusAI is a monorepo with an independent React/Vite frontend and a Python/FastAPI/PostgreSQL modular monolith under `backend/`. The authoritative product specification is `frontend/docs/CAHIER_DES_CHARGES.md`; it must remain unchanged.

## Security

- Never commit secrets, credentials, private keys, production data, or real user data.
- Use fictional accounts and sandbox-only values in tests.
- Keep authentication secrets server-side; browser sessions use HttpOnly cookies and in-memory CSRF tokens.
- Do not claim GDPR, PCI, age verification, Stripe production, AI production, or device validation without evidence.

## Architecture

- Preserve Bun and `frontend/bun.lock`.
- Backend technology is FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL, Psycopg, Pytest, HTTPX, Ruff, Docker, and Compose.
- Keep mock frontend mode independent from API mode; API errors must never silently use mock data.
- Stripe and AI integrations remain backend responsibilities and are not implemented as fake success paths.

## Database safety

- Never run Alembic downgrades, restores, `TRUNCATE`, drops, or schema recreation against the development or production database.
- Integration tests require an explicit `NEXUSAI_TEST_DATABASE_URL`, `NEXUSAI_TEST_DATABASE_NAME`, `NEXUSAI_TEST_DATABASE_ROLE`, `NEXUSAI_TEST_DATABASE_DISPOSABLE=true`, and `NEXUSAI_DEVELOPMENT_DATABASE_URL`.
- Start the disposable PostgreSQL target with `docker compose --profile test up -d postgres-test`; the test target must use its own service, network, volume, database, and role.
- The reusable database safety guard must run before destructive fixtures or migration commands; a database name containing `test` is not authorization.
- Obtain owner approval before restoring data or deleting database resources. Never delete volumes or prune Docker resources as part of tests.

## Git governance

- Work only on the authorized feature branch; never modify `main` directly.
- Preserve history and remotes.
- Never run `git push`, force-push, remote deletion, pull-request publication, merge, deployment, `git reset --hard`, or `git clean -fd`.
- Review diffs, tests, secrets, dependencies, and local commits before handoff.
