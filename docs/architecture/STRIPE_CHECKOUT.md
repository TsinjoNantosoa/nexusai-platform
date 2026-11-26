# Stripe Checkout architecture

Phase 3.2 implements one-time Sandbox Checkout for `starter` and `plus` only. The backend is authoritative for SKU, amount, currency, gem quantity, Stripe account, Product, Price, Customer, return URLs, and order ownership.

## Sequence

```text
Browser -> FastAPI: POST /billing/checkout {sku}, CSRF, Idempotency-Key
FastAPI -> PostgreSQL: validate product + account mapping; commit immutable Order
FastAPI -> Stripe: retrieve mapped Product/Price; create/reuse Customer
FastAPI -> Stripe: create Checkout Session, mode=payment, quantity=1
Stripe --> FastAPI: validate Sandbox Session, URL, customer, amount, currency, metadata
FastAPI -> PostgreSQL: persist Session/PaymentIntent and status
FastAPI --> Browser: hosted checkout_url
Browser -> Stripe: official hosted payment page
Stripe --> Browser: server-generated success/cancel return
Browser -> FastAPI: GET /billing/orders/{id}
FastAPI -> Stripe: retrieve and validate Session + one line item
FastAPI -> PostgreSQL: persist payment status only
FastAPI --> Browser: paid/pending/expired; fulfillment remains pending
```

## Lifecycle and boundaries

An `Order` is committed before any Stripe mutation. Its SKU, amount, currency, gem quantity, Stripe account, product and price IDs, request fingerprint, and idempotency key are immutable snapshots. `checkout_status` tracks local session execution (`pending`, `creating`, `created`, `unknown`); `status` tracks the order (`pending`, `paid`, `failed`, `canceled`, `expired`); `payment_status` mirrors verified Stripe payment state; `fulfillment_status` remains `pending` in Phase 3.2.

The wallet and ledger are never mutated by Checkout creation or return-page processing. A paid order is therefore not a fulfilled order.

## Customers and idempotency

`stripe_customer_mappings` is unique by authenticated user and Sandbox account. A deterministic Stripe idempotency key is stored before customer creation. `orders.idempotency_key` is globally unique and bound to the authenticated user plus the accepted SKU fingerprint. Repeating an identical request retrieves the stored session; reusing the key for another user or SKU is rejected.

External calls happen outside the local transaction. A timeout, malformed response, or persistence failure moves the attempt to `unknown`/recovery-required. The API never creates a replacement session merely because a Stripe idempotency key may have expired.

## Verification controls

- Only current account-scoped catalogue mappings are accepted.
- Live resources, wrong account mappings, inactive resources, recurring prices, amount/currency mismatches, wrong customer, session, metadata, mode, or line items fail closed.
- Checkout URLs must be HTTPS on `checkout.stripe.com`.
- Return URLs are generated from `NEXUSAI_FRONTEND_BASE_URL`; browser URLs are never accepted.
- CSRF, authenticated ownership, trusted origins, rate limiting, HttpOnly sessions, and server-side secrets remain active.

## Known limitations

Webhooks, fulfillment, wallet credit, refunds, subscriptions, Customer Portal, and live payments are excluded. The browser success page is only a status refresh. An ambiguous external result requires operator recovery; no automatic remote search or destructive cleanup is attempted.
