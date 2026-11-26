# Phase 3.1 test report

## Backend

Executed against the disposable PostgreSQL target `nexusai_test` on `127.0.0.1:56433`, with explicit database name, role, disposable authorization, and development URL safeguards:

- `backend/.venv/Scripts/ruff.exe check app migrations tests` — PASS.
- `backend/.venv/Scripts/pytest.exe tests/test_stripe_catalogue.py -q` — PASS, 10 tests.
- `backend/.venv/Scripts/pytest.exe tests -q` — PASS, 52 tests, one existing Starlette/httpx deprecation warning.
- `backend/.venv/Scripts/python.exe -m alembic ... downgrade -1` then `upgrade head` on the disposable target — PASS.
- `backend/.venv/Scripts/python.exe -m pip_audit --local` — PASS, no known vulnerabilities; the local package was skipped because it is not published on PyPI.

The tests cover disabled configuration, client options, live-account rejection, approved amounts/currency/recurrence, free exclusion, dry-run read-only behavior, reuse/idempotency, conflicting prices, partial network recovery, account-scoped replacement, persistence, wallet non-mutation, and PostgreSQL concurrency serialization. The count includes the Phase 3.0 baseline of 42 backend tests.

## Required broader validation

Frontend validation — PASS: `bun install --frozen-lockfile`, lint with 10 existing warnings, typecheck, 37 Vitest tests, and production build with 48 PWA precache entries. `bun audit` exits 1 with the two previously documented moderate transitive advisories in `glob` and `minimatch`. Compose configuration and the tracked-file secret scan both pass.
