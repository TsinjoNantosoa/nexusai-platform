# Stripe catalogue architecture

Phase 3.1 prepares a Sandbox-only Stripe catalogue for the three paid offers. The PostgreSQL `products` table remains the business source of truth for SKU, amount, currency, product type, and gem quantity. The free offer is local-only and never creates a Stripe resource.

## Approved mapping

| SKU | Stripe product | Amount | Type | Credits |
| --- | --- | ---: | --- | ---: |
| `starter` | NexusAI Starter | 299 EUR cents | one-time | 100 |
| `plus` | NexusAI Plus | 999 EUR cents | one-time | 500 |
| `premium` | NexusAI Premium | 1999 EUR cents | monthly recurring | 1500 |

The catalogue version is `nexusai-2026-11-18-v1`. Stripe products and prices receive deterministic metadata and price lookup keys. Creation requests use stable, catalogue-scoped idempotency keys; a retry discovers the same metadata before considering a new resource.

## Runtime boundary

`app.billing.stripe_client` constructs the Stripe SDK client only when the explicit command needs it. It applies the configured API version, timeout, and bounded network retries. Imports and FastAPI startup do not contact Stripe. The client rejects disabled configuration and surfaces sanitized error codes without logging credentials.

Stripe SDK 17.1.0 responses are normalized at this boundary: raw `StripeResponse` values are deserialized with `api_mode="V1"`, Stripe resources are converted recursively through `to_dict()`, and pagination yields normalized products/prices. Missing identifiers and malformed responses fail closed. An absent `livemode` field is preserved as absent; only explicit `livemode=true` is rejected.

`app.billing.catalogue` owns discovery, validation, creation planning, and persistence. It lists all pages, rejects ambiguous or live resources, refuses mismatched amounts/currencies/recurrence, and never deletes or archives unrelated resources. A PostgreSQL transaction advisory lock serializes concurrent bootstrap runs.

## Database mapping

Migration `0002_stripe_catalogue_mappings` adds `stripe_catalogue_mappings` with:

- the internal product UUID;
- the Stripe account/Sandbox identity;
- Stripe product and price IDs;
- catalogue version;
- synchronization timestamp.

Uniqueness is scoped to account, product/resource, and catalogue version. Old Sandbox mappings are retained. A replacement Sandbox therefore receives new mappings rather than reusing IDs that belonged to the expired account. The legacy `products.stripe_product_id` and `products.stripe_price_id` fields remain populated with the latest applied mapping for server-side compatibility; they are never exposed by the product API.

## Commands

Run from `backend/` after the owner has supplied private Sandbox environment variables to the backend process:

```bash
python -m alembic upgrade head
python -m app.db.seed
python -m app.billing.bootstrap --dry-run
python -m app.billing.bootstrap --apply
python -m app.billing.bootstrap --verify
python -m app.billing.bootstrap --apply
```

`--dry-run` and `--verify` do not create or persist catalogue resources. `--apply` is explicit and must be run by the owner; Codex does not run it with owner credentials. Repeating `--apply` should report reused products/prices and create no duplicates.

Checkout, webhooks, subscriptions, refunds, and wallet crediting remain outside this phase. Catalogue synchronization itself never changes wallet balances.
