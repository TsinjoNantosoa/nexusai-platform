# Phase 3.2.1 — Security Report

## Controls reviewed

- Checkout accepts only server-approved `starter` and `plus` one-time products.
- Client-provided price, gem count, quantity, and payment state are ignored.
- Free and Premium Checkout attempts are rejected.
- Orders and status endpoints require the authenticated owner; cross-account order access is rejected.
- Mutating Checkout requests require the session-bound CSRF token and `Idempotency-Key`.
- Stripe resource/account/session responses are normalized and Sandbox/live checks are applied.
- Wallet and ledger writes are not performed by Checkout creation, redirect return, or client-visible order status.
- Separate `status`, `payment_status`, and `fulfillment_status` fields prevent payment from implying fulfillment.
- Service-worker runtime caching is limited to the public root navigation; billing, wallet, and authenticated API responses are not cached.

## Secret and dependency checks

- Tracked credential-shaped scan: no non-placeholder credentials found.
- Root `.env` values were not read or displayed.
- `pip-audit --local`: exit `0`, no known vulnerabilities; the local package was skipped because it is not published on PyPI.
- `bun audit`: exit `1` with two known moderate transitive advisories:
  - `glob@11.1.0`, `GHSA-3g3m-2fjr-6pw4`, through Workbox/Vite-PWA.
  - `minimatch` variants, `GHSA-g3hv-75wg-m249`, through ESLint/TypeScript ESLint/Workbox.

The advisories remain documented inherited build/development dependency risk.
No blind major-version override was applied.

## Incident record

The first browser test ran against an enabled owner Sandbox configuration and
created one Checkout Session. This was an unauthorized test mutation under the
Phase 3.2.1 procedure. The backend was restarted with
`NEXUSAI_STRIPE_ENABLED=false`; subsequent browser and API checks returned
`503` before Stripe access.

Read-only local diagnostics after containment showed:

- One local order persisted with `checkout_status=created`, `status=pending`, `payment_status=unpaid`, and `fulfillment_status=pending`.
- No paid orders and no fulfilled orders.
- No purchase wallet entry; only fictional registration welcome entries were present.

The owner must inspect the Sandbox Dashboard and decide whether the pending
Checkout Session should be allowed to expire or be handled manually. Codex did
not call Stripe to inspect, expire, delete, refund, or otherwise mutate it.

## Security recommendation

**CONDITIONAL GO** for local code security after the customer-binding fix.
**NO-GO** for owner Sandbox payment or publication until the incident is
reviewed and the owner confirms the intended Sandbox state.
