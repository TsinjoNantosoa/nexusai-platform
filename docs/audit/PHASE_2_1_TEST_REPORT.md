# Phase 2.1 test report

> Historical report. The original migration command block records the Phase 2.1 setup and incident context; do not execute it. Use the isolated, fail-closed procedure in `README.md` and `docs/audit/PHASE_2_2_TEST_REPORT.md` for current validation.

## Backend

Run from `backend/` with the isolated Compose PostgreSQL service and `nexusai_test` database:

```powershell
$env:NEXUSAI_TEST_DATABASE_URL = "postgresql+psycopg://nexusai:nexusai@127.0.0.1:55432/nexusai_test"
$env:NEXUSAI_DATABASE_URL = "postgresql+psycopg://nexusai:nexusai@127.0.0.1:55432/nexusai"
.venv\Scripts\ruff.exe check app migrations tests
.venv\Scripts\python.exe -m alembic downgrade base
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m pytest tests -q
.venv\Scripts\python.exe -m pip_audit --local
```

Validated result: Ruff passed; migration downgrade/upgrade passed; **23 tests passed** against real PostgreSQL, including independent-connection debit, duplicate-operation, and refund concurrency tests; `pip-audit` reported no known vulnerabilities.

## Frontend

```powershell
cd frontend
bun install --frozen-lockfile
bun run lint
bun run typecheck
bun run test
bun run build
bun audit
```

Validated result: frozen install passed with no lockfile changes; lint passed with 0 errors and 10 existing Fast Refresh warnings; typecheck passed; 5 files and 37 Vitest tests passed; production build passed with 48 PWA precache entries (1109.74 KiB). `bun audit` reproducibly reports two moderate transitive build/development advisories in `glob` and `minimatch`.

## Browser and responsive checks

```powershell
cd frontend
python tests/e2e/backend_journey.py
python tests/e2e/nexus_journeys.py
python tests/e2e/responsive_journey.py --viewports 280,320,360
python tests/e2e/responsive_journey.py --viewports 375,390,414
python tests/e2e/responsive_journey.py --viewports 768,1024,1440
python tests/e2e/responsive_journey.py --viewports 1920
```

The mock financial/chat wrapper passed on Windows through `sys.executable` with zero page errors. The responsive groups passed **10 viewports x 13 routes = 130 checks**, with zero page errors and zero measured overflow. The initial serial timeout is historical and is superseded by these grouped results.

## Infrastructure evidence

- `docker compose up -d --build` produced healthy PostgreSQL/backend services in the isolated `nexusai-phase2` project.
- `/health/live` and `/health/ready` passed; readiness returned 503 while PostgreSQL was stopped and recovered after restart.
- The backend container runs as non-root; the PostgreSQL volume and project network are scoped to NexusAI.
- Migration downgrade/upgrade and backend restart persistence were validated against the isolated database; no other Docker project was modified.

Operational note: the first manual downgrade was mistakenly run against the normal `nexusai` database before the isolated target was corrected. Its schema was recreated and seeded; the earlier local development records were not recoverable. Subsequent migration validation used `nexusai_test` only.
