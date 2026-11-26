# NEXUSAI — Phase 3.2.3 Incident Closure and Demo Readiness

**Date:** 2026-11-26
**Branch:** `feat/stripe-integration`
**Scope:** read-only Stripe Sandbox incident verification, automated-test isolation and guarded demo preparation

## 1. Consolidated Decision

| Decision | Result | Explanation |
| --- | --- | --- |
| Sandbox incident | **OPEN — contained** | The single accidental Checkout Session is still `open` and `unpaid`; owner expiration or natural expiry remains required. |
| Automated-test isolation | **GO** | Tests reject inherited credentials, block Stripe network methods and use mocked gateways plus isolated PostgreSQL. |
| Local runtime | **GO** | Standard Compose is healthy, migration head is active and Stripe is fail-closed to `false`. |
| Stripe demonstration activation | **NO-GO** | The guarded launcher was prepared but not executed. |
| Manual Sandbox payment | **NO-GO** | Owner must first review the open Session and explicitly authorize a separate manual demo. |
| Phase 3.3 | **NO-GO** | Payment validation and owner acceptance are still pending. |

No Stripe resource was created, mutated, expired, refunded or paid during this phase. The only Stripe calls were the owner-authorized read-only account, Checkout Session and conditional PaymentIntent checks described below.

## 2. Git and Previous Evidence

- Branch verified: `feat/stripe-integration`.
- Starting state: clean, seven commits ahead of `origin/feat/stripe-integration`.
- Remote origin and existing history were preserved; no push, merge, reset, cleanup, deployment or remote operation was performed.
- Previous audited commits remain present, including `2ca60cb`, `91e09b5`, `5e04e37` and `f01119c`.
- The Phase 3.2.1 reports and `docs/audit/PHASE_3_2_2_FINAL_READINESS_REPORT.md` were reviewed before this implementation.

The Phase 3.2.2 report recorded the original incident: a browser validation inherited the owner Sandbox configuration and created one Checkout Session before Stripe was disabled. No card data was submitted and no local fulfillment was observed.

## 3. Stripe Read-Only Incident Evidence

The persisted local order was used to locate the associated remote Session. Stripe identifiers, Checkout URLs, raw responses, account identifiers and personal data are intentionally omitted from this report.

### Account and Session

- `GET /v1/account`: succeeded using the credential already injected in the backend container; the account identity matched the credential context and its identifier was withheld.
- The normalized account response did not expose a `livemode` field; the Checkout Session itself reported `livemode=false`.
- Session object: `checkout.session`.
- Session status: `open`.
- Payment status: `unpaid`.
- Mode: `payment`.
- Amount: `299` minor units.
- Currency: `eur`.
- PaymentIntent: absent, therefore no PaymentIntent retrieval was needed and no amount was received.
- Subscription: absent.
- Expiration: `expires_at` is present; the exact timestamp is withheld.

No Stripe mutation was attempted. Because the Session remains open and unpaid, Codex did not artificially expire it and stops closure pending the owner’s decision to leave it until natural expiry or handle it in the Dashboard.

### PostgreSQL comparison

The standard local development database was queried read-only after the Stripe check:

```text
order=65aa6286-8666-43f1-86ac-4c9e9b95e937
status=pending
payment_status=unpaid
fulfillment_status=pending
price=299 EUR cents
persisted_customer=true
persisted_session=true
paid_orders=0
fulfilled_orders=0
purchase_wallet_entries=0
catalogue_mappings=3
alembic=0003_checkout_orders
```

There is no local subscription table or subscription activation record. The evidence confirms no unauthorized successful payment, fulfillment, gem credit, subscription activation or duplicate financial effect.

## 4. Root Cause and Prevention

### Root cause

The earlier browser/API validation ran while the owner’s local environment contained `NEXUSAI_STRIPE_ENABLED=true` and owner Sandbox credentials. The original Compose mapping forwarded those variables directly to the backend, so a normal local startup could unintentionally enable the real Sandbox integration.

### Corrections implemented

- `compose.yaml` now reads Stripe activation and credentials only from dedicated `NEXUSAI_STRIPE_DEMO_*` variables and defaults to `stripe_enabled=false` with fictional placeholders.
- An owner’s ordinary `NEXUSAI_STRIPE_ENABLED=true` flag no longer activates the standard Compose backend.
- `compose.e2e.yaml` uses the isolated `nexusai_test` PostgreSQL service, a dedicated backend port, dedicated API origins and Stripe-disabled configuration with fictional credentials only.
- `backend/app/core/test_safety.py` rejects any automated test environment that enables Stripe or inherits either Stripe credential variable.
- `backend/tests/conftest.py` fails during test collection when inherited credentials are detected and blocks Stripe HTTP client methods for every automated test.
- Existing catalogue and checkout tests continue to use fake gateways and SDK objects; no automated test needs a real Stripe key.
- `frontend/tests/e2e/isolation.py` rejects direct browser journeys without the isolated mode, rejects inherited credentials and forces child journeys to Stripe-disabled mode.
- `frontend/tests/e2e/test_isolation.py` covers safe setup, missing isolated mode and inherited-credential rejection.
- `tools/start_stripe_demo.ps1` requires `-OwnerApproved`, validates Sandbox-only key formats, verifies Docker/PostgreSQL/backend health, starts API-mode frontend on `http://127.0.0.1:5173` by default, and never creates a Checkout Session automatically.
- The demo launcher removes Stripe variables before starting the frontend process.

The temporary E2E run found and fixed two isolation defects before passing: empty `SecretStr` values were replaced with fictional accepted placeholders, and the API E2E backend received its dedicated `8081` origin.

## 5. Validation Evidence

| Check | Result |
| --- | --- |
| Targeted backend security/catalogue tests | PASS, `38 passed` |
| Full backend Ruff | PASS |
| Full backend Pytest | PASS, `73 passed`, one existing Starlette/httpx warning |
| Backend `pip-audit --local` | PASS, no known vulnerabilities; local package skipped as unpublished |
| Frontend lint | PASS, 10 existing Fast Refresh warnings, no errors |
| Frontend typecheck | PASS |
| Frontend Vitest | PASS, `37 passed` |
| Frontend E2E isolation unit test | PASS, `3 tests` |
| Isolated API browser journey | PASS, registration/session/catalogue/logout against `nexusai_test` and backend `8101` |
| Frontend production build | PASS, PWA generated with 48 precache entries |
| `bun audit` | EXPECTED NON-ZERO, two previously documented moderate advisories in the build chain |
| Compose E2E configuration | PASS; test DB, dedicated port, Stripe disabled and fictional credentials |
| Standard Compose fail-closed check | PASS; owner `NEXUSAI_STRIPE_ENABLED=true` was ignored and effective Stripe state was `false` |
| Standard Docker/PostgreSQL health | PASS; backend and PostgreSQL healthy |
| Alembic | PASS: `0003_checkout_orders (head)` |
| Development DB integrity | PASS; one unpaid pending incident order, three mappings retained, no financial side effects |
| Secret scan | PASS; no non-placeholder/non-test credential-shaped value found |
| `git diff --check` | PASS before final commit |

The known Bun findings remain:

- `glob@11.1.0` through `vite-plugin-pwa` → `workbox-build`, [GHSA-3g3m-2fjr-6pw4](https://github.com/advisories/GHSA-3g3m-2fjr-6pw4).
- Workbox/ESLint/TypeScript-ESLint dependency paths containing `minimatch`, [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249).

They remain build/development-chain findings, not runtime Checkout dependencies. No blind dependency upgrade was applied.

## 6. Owner Actions Remaining

1. In the correct temporary Stripe Sandbox, locate the single open unpaid Session using the private order metadata/client reference. Do not share its URL or identifiers.
2. Confirm `livemode=false`, `open`, `unpaid`, EUR 2.99, no PaymentIntent, no subscription and no successful event.
3. Decide whether to leave it for natural expiry or expire it manually in the Dashboard. Codex will not perform that mutation.
4. Review this report and explicitly accept the isolated test design and remaining Bun advisories.
5. Only after those checks, run the guarded local mechanism from a private terminal:

   ```powershell
   .\tools\start_stripe_demo.ps1 -OwnerApproved
   ```

   The script requires private `NEXUSAI_STRIPE_SECRET_KEY` and `NEXUSAI_STRIPE_WEBHOOK_SECRET` process variables, refuses live formats, and reports the exact local shop URL without printing credentials.
6. If a manual Sandbox payment is approved, use only a Stripe test card, perform one deliberate Starter or Plus checkout, and compare the resulting order state with Stripe. Do not use a real card, live mode or production credentials.

### Owner GO criteria

- The accidental Session is identified as the only intended unpaid artifact.
- No payment, PaymentIntent, fulfillment, gem credit or subscription exists.
- The owner accepts that this phase has no webhook fulfillment implementation.
- The owner explicitly approves the separate manual Sandbox demonstration.

### Owner NO-GO criteria

- The Session is unknown, live-mode, paid or associated with any unexpected event.
- A local financial side effect exists without verified payment.
- The temporary credential is expired, ambiguous or from the wrong Sandbox.
- The owner has not completed the Dashboard review and explicit approval.

## 7. Final Phase Decision

**Incident:** OPEN but contained; awaiting owner handling of the still-open unpaid Session.  
**Isolation:** GO.  
**Local runtime:** GO.  
**Demo activation:** NO-GO until explicit owner approval.  
**Manual Sandbox payment:** NO-GO until incident review.  
**Phase 3.3:** NO-GO before owner payment validation.

No push, merge, deployment or Phase 3.3 work was performed.
