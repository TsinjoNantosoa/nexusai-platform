# NEXUSAI — Stripe Operational Recovery

**Date:** 2026-11-26
**Branch:** `feat/stripe-integration`
**Scope:** post-PR Stripe recovery, incident closure, Sandbox demo activation and owner payment readiness

## 1. Final Decisions

| Gate | Decision | Evidence |
| --- | --- | --- |
| Runtime | **GO** | Owner-approved Sandbox backend, PostgreSQL and API-mode React frontend are running locally. |
| Incident | **CLOSED** | The only persisted incident session was already `expired`, `unpaid`, `livemode=false`; no expiration mutation was needed. |
| Sandbox demonstration | **GO** | Account, catalogue, mappings, health, catalogue endpoint and pricing page were verified. |
| Manual test payment | **GO** | The owner may perform one deliberate Sandbox payment; Codex did not create a new session or pay. |
| Phase 3.3 | **NO-GO** | Remains blocked until the owner completes and accepts the manual payment validation. |

No live credential, payment, refund, new Checkout Session, subscription activation, fulfillment or wallet credit was performed by Codex.

## 2. Git and Worktree

- Current worktree: `C:\Users\Tsinjo\Documents\projet\nexusai-stripe`.
- Active worktree branch: `feat/stripe-integration`.
- The branch was clean and synchronized with `origin/feat/stripe-integration` at the start of this recovery.
- `origin/main` does not contain the Stripe branch; no merge was assumed.
- Pull Request state cannot be established from Git refs alone; no GitHub CLI/API or publication operation was used.
- Existing worktree `backup/stripe-before-sync` and all ignored configuration were preserved.
- New local changes are limited to the expired-session reconciliation fix, Stripe line-item normalization fix, launcher portability fix, regression tests and this report.
- No push, merge, reset, branch deletion, deployment or remote modification was performed.

## 3. Credential Recovery and Sandbox Verification

The original ignored root `.env` exists and contains the two required private Sandbox variables. They were parsed silently and injected only into the temporary Docker process environment. Values were never printed, logged, sent to the frontend, staged or committed.

Read-only Stripe verification succeeded:

- Sandbox account identity matched the persisted PostgreSQL Stripe account mapping.
- Remote catalogue read: `3` products and `3` prices.
- Remote products with `livemode=false`: `3/3`.
- Remote prices with `livemode=false`: `3/3`.
- PostgreSQL Stripe catalogue mappings: `3`.
- No new Sandbox or catalogue resource was created.

The standard Compose definition remains fail-closed by default. The currently running backend is enabled only because the owner-approved demo launcher injected the dedicated `NEXUSAI_STRIPE_DEMO_*` variables for this local runtime.

## 4. Incident Closure

The single persisted incident order was matched to its existing Checkout Session using the account, order metadata, customer, amount, currency and Checkout line item. Read-only Stripe verification confirmed:

- `livemode=false`.
- Session status: `expired`.
- Payment status: `unpaid`.
- PaymentIntent: absent.
- Subscription: absent.
- No successful payment, fulfillment or wallet purchase entry.

The previously authorized expiration endpoint was not called because the session had already expired. No other Stripe mutation was attempted.

The local order was reconciled through `CheckoutService`, not by direct SQL:

```text
status=expired
payment_status=unpaid
fulfillment_status=pending
checkout_status=created
```

Post-reconciliation PostgreSQL evidence:

```text
paid_orders=0
fulfilled_orders=0
purchase_wallet_entries=0
catalogue_mappings=3
alembic=0003_checkout_orders
```

## 5. Corrections Applied

Two runtime defects discovered during recovery were corrected:

- Expired Checkout Sessions may omit their Checkout URL; reconciliation now accepts that omission only for an expired session while creation and active recovery still require a valid Stripe Checkout URL.
- Stripe returns Checkout line items with `object="item"`; the client previously expected the incorrect `line_item` object name.
- The demo launcher now resolves the actual Bun executable beneath the Windows npm wrapper, allowing `Start-Process` to start the frontend reliably.

Regression coverage was added for expired-session reconciliation without a URL and actual Stripe line-item object normalization.

## 6. Runtime Validation

| Check | Result |
| --- | --- |
| Docker backend | PASS, healthy |
| PostgreSQL | PASS, healthy |
| PostgreSQL test service | PASS, healthy and preserved |
| Backend readiness | PASS, HTTP 200 at `http://127.0.0.1:8100/health/ready` |
| Backend Stripe configuration | PASS, enabled only in the owner-approved demo runtime |
| Local offers | PASS, four SKUs: `free`, `starter`, `plus`, `premium` |
| Stripe mappings | PASS, three |
| Alembic | PASS, `0003_checkout_orders` |
| React API-mode frontend | PASS, HTTP 200 |
| Pricing page | PASS at `http://127.0.0.1:5173/pricing` |
| Automated tests | PASS, targeted backend suite `30 passed` in disposable PostgreSQL |
| Previous validated suites | Reused: 73 backend tests, 37 frontend tests and E2E isolation from Phase 3.2.3 |
| Automated tests against active demo | NOT RUN, as required |
| Secret scan | PASS; no private credential values were displayed or tracked |

The frontend is intentionally running without backend Stripe credentials in its process. No purchase action was clicked or scripted.

## 7. Owner Manual Sandbox Payment

The owner may now inspect the running application:

- Application: `http://127.0.0.1:5173`
- Pricing page: `http://127.0.0.1:5173/pricing`
- Backend readiness: `http://127.0.0.1:8100/health/ready`

Recommended manual flow:

1. Open the application and register or log in with the owner’s local test account.
2. Open the pricing page and select **Starter** once.
3. Complete Checkout only with an approved Stripe Sandbox test card in the verified Sandbox account.
4. Return to the application and inspect the resulting order; do not use a live card or live mode.

Expected local state before payment:

```text
wallet_balance=20
order_status=pending
payment_status=unpaid
fulfillment_status=pending
```

Expected state after a successful Sandbox payment and local status refresh:

```text
order_status=paid
payment_status=paid
fulfillment_status=pending
wallet_balance=20
purchase_wallet_entries=0
```

The wallet must not receive gems automatically during this phase. Any unexpected credit, fulfillment, live-mode result, duplicate order, or account mismatch is an immediate NO-GO.

## 8. Remaining Risks

- Manual payment has not been performed by Codex and remains owner-controlled.
- Phase 3.2 has no authorized automatic fulfillment or gem-credit path; successful payment must not be interpreted as fulfillment.
- The two previously documented moderate `bun audit` advisories remain in the build/development dependency chain and were not upgraded blindly.
- The demo backend is intentionally enabled for the current owner-approved local session; standard Compose defaults remain disabled and must be used for automated tests.

## 9. Local Commit Recommendation

The source and test corrections plus this report require a new local commit after final `git diff --check` and targeted validation. No publication is authorized by this report.

The owner should review the resulting local commits and complete the manual payment checklist before any future Phase 3.3 work. No push, merge or deployment is recommended until that validation is accepted.
