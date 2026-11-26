# Database backup and recovery policy

This policy applies to NexusAI development and future production operations. It does not authorize Codex or automation to restore, overwrite, delete, or recreate a database.

## Development backup

Before an owner-approved development migration or data operation, create a custom-format dump and store it outside the repository. Example PowerShell command:

```powershell
New-Item -ItemType Directory -Force .\backups | Out-Null
docker compose exec -T postgres pg_dump -U nexusai -d nexusai --format=custom > .\backups\nexusai-dev-YYYYMMDD-HHmm.dump
```

The owner must replace the timestamp, verify the dump exits successfully, move it to encrypted storage outside Git, restrict access, and apply a documented retention period. The local `backups` directory is not a publication or long-term retention system.

## Future production policy

Production must use a managed PostgreSQL backup service with point-in-time recovery, encrypted scheduled dumps, separate encryption keys, tested retention, access logging, and least-privilege backup/restore roles. Credentials belong in an approved secret manager, never in Compose files, shell history, repository files, or reports.

## Restore procedure

1. Obtain explicit owner approval, identify the incident, choose the recovery point, and preserve the source database.
2. Restore into a newly provisioned isolated database and role. Never use `--clean`, `dropdb`, or an overwrite against the existing development or production target.
3. Verify `current_database()` and `current_user`, connectivity, migration version, table counts, constraints, and representative fictional records.
4. Run application read-only checks and reconciliation before any controlled cutover. Record the dump checksum, operator, time, target identity, and validation results.
5. Retain the original source and recovery artifacts until the owner closes the incident.

The disposable test service may be used for a restore rehearsal only when it is explicitly authorized and remains isolated. Alembic downgrade, schema recreation, cleanup, and restore tests are prohibited against development and production.

## Incident-001 status

No pre-incident backup was available for the Phase 2.1 local development reset. The exact prior rows remain unknown and no recovery is claimed. The incident record is `docs/audit/INCIDENT_001_DATABASE_ISOLATION.md`.
