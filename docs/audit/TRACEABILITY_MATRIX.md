# NexusAI requirement traceability matrix — Phase 3.2

The authoritative requirements remain in `frontend/docs/CAHIER_DES_CHARGES.md`, which is unchanged.

| Requirement | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| F01 registration/login/logout | IMPLEMENTED | FastAPI auth routes, Argon2id, session tests | Email verification and password reset are deferred. |
| F02 profile/session | IMPLEMENTED | `/users/me`, expiry/revocation, HttpOnly cookie tests | Production TLS topology remains to validate. |
| F03 catalogue | IMPLEMENTED | PostgreSQL products, idempotent seed, `/billing/products`, Phase 3.1 Stripe catalogue bootstrap and account-scoped mappings | Subscription catalogue remains display-only. |
| F06 wallet/ledger | IMPLEMENTED | Atomic wallet service, immutable entries, row locks, concurrency tests | Paid credit workflows are deferred to Phase 3. |
| F12 admin access | PARTIAL | Server-side role dependency and denied regular-user test | Moderation persistence/workflows are deferred. |
| S01 password/session security | IMPLEMENTED | Argon2id, token hashes, expiry, revocation, rotation, secure production validation | Email/password recovery is deferred. |
| S02 CSRF/RBAC/ownership | IMPLEMENTED | CSRF bootstrap, origin checks, admin dependency, session-derived wallet ownership | Production CSP and distributed deployment remain. |
| S06 abuse protection | PARTIAL | Deterministic process-local auth sliding window, 429, recovery, forwarded-header bypass test | Shared rate limiting is required for multiple instances. |
| DB migrations | IMPLEMENTED | Alembic upgrade, downgrade, upgrade against PostgreSQL | No automatic schema creation in the application. |
| Local infrastructure | IMPLEMENTED | Project-specific Compose network, volume, healthchecks, non-root backend, restart persistence validation | Production orchestration is out of scope. |
| Stripe Checkout | IMPLEMENTED / PARTIAL | Server-authoritative hosted Checkout, durable orders/customers, idempotency, ownership/status tests | Webhooks, wallet fulfillment, subscriptions, refunds, live payments, and owner E2E remain deferred. |
| Frontend API mode | IMPLEMENTED | CSRF bootstrap/rotation in `HttpApiClient`, real browser journey | Mock mode remains independent. |

## Evidence

- Backend unit and PostgreSQL integration tests: `backend/tests/`.
- Real frontend API-mode journey: `frontend/tests/e2e/backend_journey.py`.
- Frontend Phase 1.1 evidence: `frontend/docs/audit/TRACEABILITY_MATRIX.md` and its historical reports.

## Phase 2.1 acceptance matrix

| ID | Test file / command | Test function or assertion | Result | Remaining limitation |
| --- | --- | --- | --- | --- |
| AUTH-01 | `backend/tests/test_integration.py` | `test_registration_grants_exactly_one_welcome_bonus`: registration, user role, wallet 20, one entry | PASS | Email verification deferred |
| AUTH-02 | `frontend/tests/e2e/backend_journey.py` | Register, reload, protected wallet, pricing, logout browser journey | PASS | Production identity provider not used |
| AUTH-03 | `backend/tests/test_integration.py` | `test_logout_revokes_session_and_accounts_are_isolated`: revoked session returns 401 | PASS | Session store is PostgreSQL only |
| AUTH-04 | `backend/tests/test_integration.py` | `test_csrf_rejects_invalid_tokens_without_mutation`: bootstrap and forbidden origin return expected errors | PASS | Deployment CSP/TLS not tested |
| AUTH-05 | `backend/tests/test_integration.py` | `test_expired_sessions_cannot_access_protected_resources`: expired session cannot access user or wallet routes | PASS | Clock control is fixture-level |
| AUTH-06 | `backend/tests/test_integration.py` | `test_regular_users_cannot_access_admin_routes`: user receives 403 | PASS | Admin workflows deferred |
| AUTH-07 | `backend/tests/test_integration.py` | `test_csrf_rejects_invalid_tokens_without_mutation`: missing, empty, invalid, cross-session, valid, revoked cases | PASS | No browser-specific CSRF test beyond API journey |
| AUTH-08 | `backend/tests/test_integration.py` | `test_login_rotates_session_and_csrf_tokens`: new cookies replace old and old session returns 401 | PASS | Cookie behavior still needs production TLS validation |
| AUTH-09 | `backend/tests/test_integration.py` | `test_cross_account_wallet_resources_use_authenticated_ownership`: identifiers cannot cross wallet ownership | PASS | No administrative cross-wallet feature exists |
| AUTH-10 | `backend/tests/test_integration.py` | `test_auth_rate_limit_enforces_window_and_ignores_forwarded_header_bypass`: 429, independent key, recovery, XFF resistance | PASS | Limiter is process-local |
| WAL-01 | `backend/tests/test_integration.py` | Registration creates one wallet and exact 20-gem welcome ledger entry | PASS | Paid credits deferred |
| WAL-02 | `backend/tests/test_integration.py` | `test_welcome_replay_cannot_create_a_second_wallet_or_entry`: unique wallet failure leaves one wallet/entry and balance 20 | PASS | Concurrent welcome replay is represented by database uniqueness, not a thread test |
| WAL-03 | `backend/tests/test_integration.py` | `test_internal_credit_is_atomic_idempotent_and_rejects_conflicts`: +5, exact entry, replay, conflict | PASS | Service is not a public API |
| WAL-04 | `backend/tests/test_integration.py` | `test_wallet_operations_are_idempotent_and_refunds_are_bounded`: signed debit changes balance | PASS | No product settlement yet |
| WAL-05 | `backend/tests/test_integration.py` | `test_concurrent_debits_never_make_balance_negative`: one success, one insufficient balance, invariant holds | PASS | PostgreSQL-only evidence |
| WAL-06 | `backend/tests/test_integration.py` | `test_wallet_operations_are_idempotent_and_refunds_are_bounded`: duplicate debit returns same entry | PASS | Reference uniqueness is global |
| WAL-07 | `backend/tests/test_integration.py` | `test_concurrent_duplicate_operations_create_one_entry`: two connections create one ledger entry | PASS | Two-worker local test only |
| WAL-08 | `backend/tests/test_integration.py` | `test_wallet_operations_are_idempotent_and_refunds_are_bounded`: full refund restores balance | PASS | Webhook reconciliation deferred |
| WAL-09 | `backend/tests/test_integration.py` | `test_partial_refunds_remain_bounded_and_conserve_the_ledger`: 2 + 4 refunds equal 6 debit | PASS | No external refund provider |
| WAL-10 | `backend/tests/test_integration.py` | Wallet/refund tests cover same-reference replay, conflicting replay, excess, and concurrent refund | PASS | Refund policy remains internal |
| WAL-11 | `backend/tests/test_integration.py` | Wallet tests assert `balance == SUM(entries.amount)` after credit, debit, refund, reject, rollback, and concurrency | PASS | Integer invariant only; no reconciliation job |
| WAL-12 | `backend/tests/test_integration.py` | `test_cross_account_wallet_resources_use_authenticated_ownership`: separate balances/history and forged user ID remain isolated | PASS | No admin wallet view |
| WAL-13 | `backend/tests/test_integration.py` | `test_public_clients_cannot_credit_wallets`: arbitrary public credit returns 404 | PASS | Payment credits deferred |
| WAL-14 | `backend/tests/test_integration.py` | Internal/cross-wallet reuse of reference with conflicting amount/type/owner returns idempotency conflict | PASS | Reference contract remains internal |
| INF-01 | `backend/` Alembic commands | `alembic downgrade base` then `upgrade head` succeeds on PostgreSQL | PASS | No automatic production migration policy |
| INF-02 | `backend/tests/test_integration.py` | `test_health_and_products_are_available` plus live/readiness Docker checks | PASS | No external monitoring |
| INF-03 | `compose.yaml` Docker commands | Isolated `nexusai-phase2` network/volume, healthy services, non-root backend | PASS | Production orchestration deferred |
| INF-04 | Docker restart validation | Backend restart preserves existing fictional accounts and wallet data | PASS | Backup/restore not tested |
| INF-05 | Frontend Bun/Playwright commands | 37 Vitest tests, build/PWA output, API journey, mock journeys, and 130 responsive checks pass | PASS | Physical Android/iOS installation not tested |

Total: **29/29 PASS** for the local Phase 2.1 acceptance scope. Limitations above remain explicit and do not constitute production-readiness claims.

## Phase 3.3 addendum

| Requirement | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Signed Stripe webhook intake | IMPLEMENTED | Raw-body signature verification, timestamp tolerance, body limit, live/account rejection, durable inbox | Owner CLI forwarding remains manual |
| One-time wallet fulfillment | IMPLEMENTED | Server-side Checkout/Price/PaymentIntent verification, atomic ledger transaction and Starter/Plus tests | Premium subscriptions and refunds remain deferred |
| Financial idempotency | IMPLEMENTED | Account-scoped event uniqueness and PaymentIntent-derived wallet reference | Real Stripe delivery remains owner validation |
| Historical reconciliation | IMPLEMENTED / CONTROLLED | Read-only candidate listing and targeted approval-gated apply CLI | Codex did not apply a historical order |

Phase 3.3 implementation is complete locally. It must not be treated as a real Stripe demonstration until the owner performs and accepts an authorized Sandbox webhook delivery.

## Phase 2.2 database safety matrix

| ID | Control / evidence | Result | Boundary |
| --- | --- | --- | --- |
| DBSAFE-01 | `postgres-test` has a separate Compose service, network, volume, database, role, and host port | PASS | Disposable local infrastructure only |
| DBSAFE-02 | `backend/app/db/safety.py` requires explicit test URL, database name, role, and `DISPOSABLE=true` | PASS | Configuration is local and operator-supplied |
| DBSAFE-03 | Pytest fixtures and destructive Alembic commands reject development/production targets before destructive SQL | PASS | Effective host/port are established by isolated service topology; PostgreSQL identity query verifies database and role |
| DBSAFE-04 | Nine unit tests cover missing configuration, declared development target, name-only authorization, dev/prod rejection, role mismatch, effective identity mismatch, no-SQL-on-rejection, accepted disposable target, and command classification | PASS | No production database is contacted |
| DBSAFE-05 | Incident review and backup/recovery policy are recorded | PARTIAL | No pre-incident backup or restore execution was available; owner approval is required for recovery |
| DBSAFE-06 | Backend regression passes with the isolated PostgreSQL target and development database identity remains unchanged by test operations | PASS | Frontend regression evidence remains from Phase 2.1 |

## Phase 3.2 acceptance evidence

| ID | Evidence | Result | Boundary |
| --- | --- | --- | --- |
| STR32-01 | Migration `0003_checkout_orders`, model constraints, isolated upgrade | PASS | No downgrade or production migration executed |
| STR32-02 | Extended single normalized Stripe gateway and fake-gateway tests | PASS | No owner Sandbox call by Codex |
| STR32-03 | Server product/mapping resolution and immutable order snapshot tests | PASS | Catalogue must be bootstrapped by owner |
| STR32-04 | CSRF/auth/rate limit/hosted URL/session validation implementation | PASS | Process-local limiter |
| STR32-05 | Durable idempotency and recovery states; duplicate/conflict tests | PASS | Ambiguous remote outcomes require operator recovery |
| STR32-06 | Owned order status endpoint, payment/fulfillment separation, line-item verification | PASS | No fulfillment/webhook business processing |
| STR32-07 | API-mode frontend navigation, bounded polling, offline blocking, bilingual strings | PASS | Responsive browser checks remain a final gate |
| STR32-08 | Service worker remains public-shell-only; no payment mutation queue | PASS | Published PWA inspection remains owner validation |

Phase 3.3 must not begin until the owner completes final validation and explicitly authorizes it.
