# Phase 2 test report

## Backend commands

```powershell
Set-Location backend
$env:NEXUSAI_TEST_DATABASE_URL = "postgresql+psycopg://nexusai:nexusai@localhost:55432/nexusai_test"
$env:NEXUSAI_DATABASE_URL = "postgresql+psycopg://nexusai:nexusai@localhost:55432/nexusai"
.venv\Scripts\ruff.exe check app migrations tests
.venv\Scripts\alembic.exe downgrade base
.venv\Scripts\alembic.exe upgrade head
.venv\Scripts\python.exe -m pytest tests -q
```

The original Phase 2 run passed Ruff, migration downgrade/upgrade, and 12 tests against real PostgreSQL. Phase 2.1 supersedes that count with 23 tests and adds expiry, token rotation, invalid-CSRF variants, ownership isolation, rate limiting, welcome replay, internal credits, partial and concurrent refunds, explicit ledger invariants, and contradictory idempotency coverage.

The browser API-mode journey `frontend/tests/e2e/backend_journey.py` passed registration, session restoration, wallet balance, catalogue access, and logout through the Vite proxy.

## Frontend regression

- `bun install --frozen-lockfile`: passed with no lockfile changes.
- `bun run lint`: passed with 0 errors and 10 existing Fast Refresh warnings.
- `bun run typecheck`: passed.
- `bun run test`: 5 files and 37 tests passed.
- `bun run build`: passed; PWA precache contains 48 entries (1109.74 KiB).
- Existing financial and chat journeys passed with no reported page errors.
- The initial serial responsive command exceeded the five-minute runner limit. Phase 2.1 superseded it with four independent groups covering 10 viewports × 13 routes = 130 checks; every group passed with zero overflow offenders and zero page errors.

## Security and dependency checks

- Secret filename/content scans found no tracked credentials or private-key material; local `.env` files remain ignored.
- `frontend/docs/CAHIER_DES_CHARGES.md` is unchanged from `origin/main`.
- `bun audit` reproduces two moderate transitive build/development advisories in `glob` and `minimatch`; no compatible targeted fix was applied without forcing an incompatible Workbox/Vite-PWA major upgrade.
