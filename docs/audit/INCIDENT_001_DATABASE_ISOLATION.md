# INCIDENT-001 — Development database targeted by migration validation

Date: 2026-11-26
Severity: **SEV-2 equivalent — local development data loss; no production impact found**
Status: Contained; owner review required
Branch: `feat/backend-foundation`

## Summary

During Phase 2.1 migration validation, a downgrade intended for a disposable test database was run against the normal local development database. The command path was started from the repository root after `docker compose up -d --build`:

```text
docker compose exec -T backend python -m alembic downgrade base
```

The backend Compose environment pointed at the `postgres` service, database `nexusai`, and role `nexusai` on the `nexusai_phase2_postgres` volume. The operation removed the development schema. The subsequent seed attempt reported that `products` did not exist; the schema was recreated and the service was recovered locally.

The intended target was a disposable test database, but the earlier setup reused the development PostgreSQL service and role. No restore was performed and no recovery artifact was found.

## Impact and evidence

- Schema reset of the local development database is confirmed.
- The earlier Phase 2.1 report recorded 8 users before the incident. After recreation and reseeding, the database contained 1 fictional user, 1 wallet, 1 wallet entry, and 4 products.
- The exact prior rows and data are **UNKNOWN** and are not claimed to be recovered.
- No database dump, snapshot, or backup artifact was found in the repository or the inspected Docker resources.
- Read-only inspection found only NexusAI containers plus `welcome-to-docker` running; no command targeted unrelated Docker projects or volumes.
- No evidence of a production database, production credentials, or production data being contacted was found.

## Why safeguards failed

1. The Compose backend had a development database URL and no separate test service.
2. Pytest could skip when the test URL was missing instead of failing closed.
3. The migration environment had no destructive-command guard.
4. Migration configuration could overwrite a programmatically selected test URL with the default settings URL.
5. The development and test paths shared PostgreSQL infrastructure and identity assumptions.

## Corrective actions

- Added the profile-only `postgres-test` service with a separate network, volume, database, role, and port.
- Added explicit `NEXUSAI_TEST_DATABASE_URL`, `NEXUSAI_TEST_DATABASE_NAME`, `NEXUSAI_TEST_DATABASE_ROLE`, and `NEXUSAI_TEST_DATABASE_DISPOSABLE=true` requirements.
- Added a reusable guard for static configuration and effective `current_database()` / `current_user` identity.
- Applied the guard before destructive pytest cleanup and Alembic `downgrade` or `stamp` paths.
- Corrected Alembic URL precedence so `-x database_url` and explicit environment configuration are not overwritten.
- Added regression tests and documented backup/recovery procedures.

## Recovery and owner decision

No restoration is possible from the current workspace without an external backup or owner-provided artifact. Do not attempt to recreate, overwrite, restore, or delete the development database as an automated follow-up. The owner must decide whether the recreated local state is acceptable or provide an approved recovery source.

Phase 3 must not begin until the owner reviews this incident, confirms the isolated test topology, and accepts the documented limitations.
