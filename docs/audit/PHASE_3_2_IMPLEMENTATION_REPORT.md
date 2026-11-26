# Phase 3.2 implementation report

## Scope

Implemented secure one-time Stripe Sandbox Checkout for `starter` and `plus`. Premium subscription Checkout, wallet fulfillment, webhooks, refunds, Customer Portal, live payments, and card handling inside NexusAI remain excluded.

## Changes

- Added migration `0003_checkout_orders` for `orders` and account-scoped `stripe_customer_mappings`.
- Extended the existing Stripe client with Product/Price validation, Customer create/retrieve, Checkout Session create/retrieve, and line-item retrieval using the pinned SDK and normalization boundary.
- Replaced the billing Checkout stub with authenticated, CSRF-protected, rate-limited, server-priced session creation.
- Added durable idempotency, ownership, account, URL, amount, currency, customer, metadata, mode, and line-item checks.
- Added `GET /billing/orders` and `GET /billing/orders/{order_id}` with separate payment and fulfillment statuses.
- Connected API-mode Starter/Plus buttons to hosted Checkout, bounded return polling, error handling, offline blocking, and Premium unavailability. Mock mode remains independent.
- Kept wallet and ledger unchanged during all Checkout and return processing.

## API contract

`POST /api/v1/billing/checkout` requires an authenticated session, valid CSRF token, `Idempotency-Key`, and body `{ "sku": "starter" | "plus" }`. It returns `{ "order_id": "UUID", "checkout_url": "https://checkout.stripe.com/..." }`.

`GET /api/v1/billing/orders/{order_id}` requires ownership and returns `status`, `paymentStatus`, `fulfillmentStatus`, `sku`, `gems`, `priceCents`, `currency`, and `createdAt`. A paid response does not fulfill or credit gems.

## Security and recovery

Orders are persisted before remote mutations. Customer/session creation uses durable, stable keys. Ambiguous external outcomes become recovery-required; the API does not blindly create another session. Secrets stay server-side, metadata is minimal, redirect URLs are server-generated, and all resources must be Sandbox resources.

## Remaining limitations

No webhook can advance fulfillment. No automated search resolves an unknown external result. Process-local rate limiting is not a distributed limiter. Final real Sandbox Checkout and payment validation require the owner.
