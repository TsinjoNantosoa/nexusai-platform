# Phase 2.2 database safety report

Date: 2026-11-26
Branch: `feat/backend-foundation`
Scope: database isolation, destructive-operation controls, incident review, and quality gate

## Outcome

Phase 2.2 implements a fail-closed disposable PostgreSQL test path. The normal development database is no longer an acceptable target for destructive fixtures or destructive Alembic commands. The Phase 2.1 incident remains an accepted local-data-loss event with no recovery claim; see `docs/audit/INCIDENT_001_DATABASE_ISOLATION.md`.

## Implemented controls

- `compose.yaml` defines a profile-only `postgres-test` service with an independent database, role, network, volume, and host port.
- `backend/app/db/safety.py` validates PostgreSQL URL, explicit database name, explicit role, explicit disposable authorization, declared development URL, known development/production separation, and effective database/role identity.
- `backend/tests/conftest.py` fails when test configuration is missing or points at the development target. Cleanup and migration setup validate the target before SQL is executed.
- `backend/migrations/env.py` honors explicit `-x database_url` and environment URLs and guards destructive online commands before migration execution.
- Unit tests prove rejection for missing configuration, undeclared development target, test-name-only authorization, development/production targets, role mismatch, effective identity mismatch, and no SQL after static rejection.

## Isolation evidence

The disposable service reports `nexusai_test` as `current_database()` and `nexusai_test` as `current_user`; it is separate from the development service (`nexusai` / `nexusai`). Authorized downgrade/upgrade validation succeeded only against the disposable service. A development-target downgrade was rejected before destructive SQL, and the development Alembic version remained unchanged across the Phase 2.2 validation.

The effective identity query does not rely on PostgreSQL exposing a server port. Host and port separation is established by the explicit configured URL and separate Compose service/network topology; database and role identity are checked from the live connection.

## Incident status

The Phase 2.1 downgrade reset the local development schema. The prior 8-user state was not recoverable from this workspace; the recreated state is not a recovery. No production impact was found. No further destructive operation was run against the normal development database during Phase 2.2.

## Quality-gate decision

- Database isolation: **PASS**, subject to owner review of the local Compose topology and environment variables.
- Destructive-operation guard: **PASS** for tested fixture and Alembic paths.
- Backup/recovery readiness: **PARTIAL** because no pre-incident backup existed and restore execution was not authorized.
- Phase 3: **CONDITIONAL NO-GO** until the owner accepts the incident and performs final validation. No Phase 3 implementation was started.
