# Phase 2 test report

## Backend commands

```powershell
Set-Location backend
$env:NEXUSAI_TEST_DATABASE_URL = "postgresql+psycopg://nexusai:nexusai@localhost:55432/nexusai_test"
$env:NEXUSAI_DATABASE_URL = "postgresql+psycopg://nexusai:nexusai@localhost:55432/nexusai"
.venv\Scripts\ruff.exe check app migrations tests
.venv\Scripts\alembic.exe downgrade base
.venv\Scripts\alembic.exe upgrade head
.venv\Scripts\pytest.exe tests -q
```

The validated run passed Ruff, migration downgrade/upgrade, and 12 tests against real PostgreSQL. Coverage includes registration bonus, duplicate email, generic credentials, CSRF, logout revocation, admin denial, product seed idempotency, wallet idempotency, bounded refund, concurrent spending, and concurrent duplicate operations.

The browser API-mode journey `frontend/tests/e2e/backend_journey.py` passed registration, session restoration, wallet balance, catalogue access, and logout through the Vite proxy.

## Frontend regression

- `bun install --frozen-lockfile`: passed with no lockfile changes.
- `bun run lint`: passed with 0 errors and 10 existing Fast Refresh warnings.
- `bun run typecheck`: passed.
- `bun run test`: 5 files and 37 tests passed.
- `bun run build`: passed; PWA precache contains 48 entries (1109.74 KiB).
- Existing financial and chat journeys passed with no reported page errors.
- The final responsive matrix was attempted across 10 viewports and 13 routes per viewport, but exceeded the five-minute runner limit before producing a result; it is therefore not claimed as passed.

## Security and dependency checks

- Secret filename/content scans found no tracked credentials or private-key material; local `.env` files remain ignored.
- `frontend/docs/CAHIER_DES_CHARGES.md` is unchanged from `origin/main`.
- `bun audit` reports two moderate transitive advisories in `glob` and `minimatch`; these remain a conditional-release risk.
