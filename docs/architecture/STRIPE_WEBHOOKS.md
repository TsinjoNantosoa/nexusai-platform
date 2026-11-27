# Stripe Webhooks

Phase 3.3 receives Stripe Sandbox events at
`POST /api/v1/billing/webhooks/stripe`.

## Intake

The endpoint reads the original request bytes, enforces the configured
`NEXUSAI_STRIPE_WEBHOOK_MAX_BODY_BYTES` limit, and verifies `Stripe-Signature`
with the pinned Stripe SDK and a non-zero timestamp tolerance. It rejects
missing/invalid/expired signatures, malformed events, live events, and account
mismatches. It does not use browser sessions or CSRF tokens; the Stripe
signature is the endpoint authentication mechanism.

Only a minimal inbox record is stored: internal UUID, account, Stripe event ID,
event type, related resource ID, lifecycle timestamps, retry count, and a
sanitized error code. Raw payloads and secrets are not logged or persisted.
Account/event uniqueness is enforced by PostgreSQL.

## Lifecycle

1. Signature verification and structural validation happen before persistence.
2. A durable `received` row is committed before HTTP 200 is returned.
3. `backend/app/billing/worker.py` claims one event with `FOR UPDATE SKIP LOCKED`.
4. Abandoned processing rows are reclaimable after the configured timeout.
5. Stripe resources are retrieved and verified server-side before fulfillment.
6. Retryable failures use bounded exponential backoff; terminal failures become
   `failed` and financial inconsistencies become `review`.

Supported events are `checkout.session.completed`,
`checkout.session.async_payment_succeeded`,
`checkout.session.async_payment_failed`, and `checkout.session.expired`.
Unsupported events are durably acknowledged without a financial effect.
Subscriptions, invoices and refunds remain outside Phase 3.3.

## Operations

The standard Compose stack keeps Stripe disabled. Start the worker only through
the explicit `stripe-demo` profile after the owner injects Sandbox credentials
and the account ID. A terminal event can be manually replayed with
`python -m app.billing.worker --replay <internal-event-uuid> --once`; replay
does not bypass signature intake or idempotent wallet references.
