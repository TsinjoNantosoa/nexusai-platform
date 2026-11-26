# Database schema

Migration `0001_initial` creates `users`, `sessions`, `wallets`, `wallet_entries`, `products`, and `audit_logs`.

- UUID primary keys and UTC-aware timestamps are used throughout.
- User email is normalized to lowercase and unique.
- A wallet is unique per user and has a database `balance >= 0` constraint.
- Wallet entries contain signed integer movements, a unique business reference, operation type, optional original reference, metadata, and creation time.
- Monetary catalogue values are integer EUR cents: 299, 999, and 1999.
- Foreign keys use explicit delete behavior; indexes cover sessions, wallet history, and audit chronology.

Future payment, conversation, AI request, subscription, and Stripe event tables are not created until their approved contracts are implemented.

## Environment topology

- Development uses the `postgres` Compose service, database `nexusai`, role `nexusai`, network `nexusai_phase2`, and volume `nexusai_phase2_postgres`.
- Disposable integration tests use the profile-only `postgres-test` service, database `nexusai_test`, role `nexusai_test`, network `nexusai_phase2_test`, and volume `nexusai_phase2_test_postgres`.
- Production is not configured in this repository. Its database URL, role, credentials, and recovery controls must be provisioned separately and must never be reused by tests.
- Test fixtures and destructive Alembic paths require explicit test URL, database name, role, disposable authorization, and a declared development URL. They verify the effective database and role before issuing destructive SQL.
- A database name containing `test` is not sufficient isolation. The service, network, volume, identity, and explicit authorization must all match.
