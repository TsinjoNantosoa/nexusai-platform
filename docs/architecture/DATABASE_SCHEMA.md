# Database schema

Migration `0001_initial` creates `users`, `sessions`, `wallets`, `wallet_entries`, `products`, and `audit_logs`. Migration `0002_stripe_catalogue_mappings` adds account-scoped, versioned Stripe product/price mappings. Migration `0003_checkout_orders` adds durable Stripe customer mappings and hosted Checkout orders.

- UUID primary keys and UTC-aware timestamps are used throughout.
- User email is normalized to lowercase and unique.
- A wallet is unique per user and has a database `balance >= 0` constraint.
- Wallet entries contain signed integer movements, a unique business reference, operation type, optional original reference, metadata, and creation time.
- Monetary catalogue values are integer EUR cents: 299, 999, and 1999.
- The free product remains local-only; paid Stripe mappings are unique by account, resource, and catalogue version.
- Stripe customer mappings are unique per user and Sandbox account; ambiguous customer creation is retained as `unknown` and never recreated automatically.
- Orders preserve immutable SKU, amount, currency, gem, account, product, price, customer, and idempotency snapshots. `status`/`payment_status` are separate from `fulfillment_status`.
- Checkout sessions and payment intents are unique within their Stripe account. Order creation commits before Stripe mutations; an uncertain external result is retained for recovery.
- Foreign keys use explicit delete behavior; indexes cover sessions, wallet history, and audit chronology.

Subscription, refund, webhook-event, conversation, and AI request tables are not created until their approved contracts are implemented. Phase 3.2 never mutates wallets or ledger entries.

## Environment topology

- Development uses the `postgres` Compose service, database `nexusai`, role `nexusai`, network `nexusai_phase3_stripe`, and volume `nexusai_phase3_stripe_postgres`.
- Disposable integration tests use the profile-only `postgres-test` service, database `nexusai_test`, role `nexusai_test`, network `nexusai_phase3_stripe_test`, and volume `nexusai_phase3_stripe_test_postgres`.
- Production is not configured in this repository. Its database URL, role, credentials, and recovery controls must be provisioned separately and must never be reused by tests.
- Test fixtures and destructive Alembic paths require explicit test URL, database name, role, disposable authorization, and a declared development URL. They verify the effective database and role before issuing destructive SQL.
- A database name containing `test` is not sufficient isolation. The service, network, volume, identity, and explicit authorization must all match.
