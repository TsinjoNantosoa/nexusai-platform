# Wallet ledger

The wallet is authoritative on the server. The initial balance is 20 gems and is represented by exactly one `welcome:<user_uuid>` entry. Public clients have no credit endpoint.

Internal movement services lock the wallet row with PostgreSQL `SELECT ... FOR UPDATE`, check the existing unique operation reference after acquiring the lock, reject contradictory retries, apply the signed integer movement, and flush the ledger entry in the same transaction. The database constraint prevents negative balances.

Refunds are compensating credits. They reference an original negative movement and sum prior restitution entries so the total refund cannot exceed the original debit. Financial history is append-only at the application level.

The current API exposes the wallet and bounded offset pages of transaction history. Product credits from paid orders are not active until Phase 3 payment verification exists.
