# Wallet Fulfillment

Starter grants exactly 100 gems and Plus grants exactly 500 gems. Premium and
all subscription events grant nothing in Phase 3.3.

Before a credit, the processor verifies the Sandbox Checkout Session, immutable
order snapshot, owner/customer, one line item, expected Price ID, integer amount,
EUR currency, one-time mode, and a succeeded PaymentIntent. Browser metadata
and client amounts are never authoritative.

Fulfillment uses one PostgreSQL transaction:

1. Lock the inbox event and order.
2. Lock the user's wallet through the existing wallet service.
3. Insert the immutable positive ledger entry.
4. Update the materialized wallet balance.
5. Mark the order fulfilled and the event completed.

The purchase reference is derived from the account and PaymentIntent, so a
second event for the same payment returns the existing movement instead of
creating another credit. A rollback leaves the order, wallet and ledger
unchanged. Paid orders never regress because a later expired or failed event
arrives. Inconsistent state is marked `review` and receives no credit.

Historical paid orders are not automatically fulfilled. The reconciliation CLI
supports read-only candidate listing and targeted dry-run verification. Apply
requires `--order-id`, `--apply`, and an explicit owner approval environment
variable; it uses the same verification and fulfillment transaction.
