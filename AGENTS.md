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

## Git governance

- Work only on the authorized feature branch; never modify `main` directly.
- Preserve history and remotes.
- Never run `git push`, force-push, remote deletion, pull-request publication, merge, deployment, `git reset --hard`, or `git clean -fd`.
- Review diffs, tests, secrets, dependencies, and local commits before handoff.
