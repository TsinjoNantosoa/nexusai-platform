# Database schema

Migration `0001_initial` creates `users`, `sessions`, `wallets`, `wallet_entries`, `products`, and `audit_logs`.

- UUID primary keys and UTC-aware timestamps are used throughout.
- User email is normalized to lowercase and unique.
- A wallet is unique per user and has a database `balance >= 0` constraint.
- Wallet entries contain signed integer movements, a unique business reference, operation type, optional original reference, metadata, and creation time.
- Monetary catalogue values are integer EUR cents: 299, 999, and 1999.
- Foreign keys use explicit delete behavior; indexes cover sessions, wallet history, and audit chronology.

Future payment, conversation, AI request, subscription, and Stripe event tables are not created until their approved contracts are implemented.
