# Phase 2.2 test report

Date: 2026-11-26
Branch: `feat/backend-foundation`

## Backend validation

The backend suite was run with the separate disposable PostgreSQL service and fictional sandbox credentials supplied through environment variables. Credential values are intentionally omitted here.

| Check | Result |
| --- | --- |
| Ruff on `app`, `migrations`, and `tests` | PASS |
| Database safety unit tests | PASS — 9 tests |
| Full backend PostgreSQL suite | PASS — 32 tests |
| `pip-audit --local` | PASS — no known backend vulnerabilities |
| Development-target destructive Alembic command | PASS — rejected before destructive SQL |
| Disposable-target downgrade then upgrade | PASS — authorized test database only |
| Development Alembic identity before/after test cycle | PASS — unchanged |

The full command setup is documented in `README.md`; it requires `NEXUSAI_TEST_DATABASE_URL`, `NEXUSAI_TEST_DATABASE_NAME`, `NEXUSAI_TEST_DATABASE_ROLE`, `NEXUSAI_TEST_DATABASE_DISPOSABLE=true`, and `NEXUSAI_DEVELOPMENT_DATABASE_URL`. Missing configuration fails rather than skipping or falling back to development.

## Prior frontend regression evidence

Phase 2.1 recorded 37 frontend tests, lint, typecheck, build, API and mock browser journeys, and 130 responsive checks. No frontend source or dependency was changed in Phase 2.2. `bun audit` continues to report the two previously documented moderate transitive advisories in `glob` and `minimatch`; this is not represented as a clean audit.

## Security and scope checks

- Secret review found no committed credentials, private keys, or production data; test values are fictional sandbox values.
- No remote Git operation was performed.
- No destructive operation was run against the normal development database during Phase 2.2.
- No backup or restore was executed; the incident report makes no recovery claim.

## Remaining limitations

The development database contains the recreated local state described in `INCIDENT_001_DATABASE_ISOLATION.md`, not the pre-incident state. Production database provisioning, managed backups/PITR, secret management, and a restore drill remain owner-operated work and are not claims of this phase.

## Browser rerun note

A fresh Phase 2.2 rerun of the browser scripts did not complete: the API journey timed out waiting for the wallet navigation, and the mock/responsive sequence timed out before reporting results. The controlled servers returned HTTP 200, but their active runtime configuration was not established by the scripts. These attempts are not counted as new passes; the prior Phase 2.1 evidence remains 37 frontend tests and 130 responsive checks. The owner should rerun the journeys with explicitly controlled mock/API Vite processes before publication.
