# NexusAI requirement traceability matrix — Phase 2

The authoritative requirements remain in `frontend/docs/CAHIER_DES_CHARGES.md`, which is unchanged.

| Requirement | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| F01 registration/login/logout | IMPLEMENTED | FastAPI auth routes, Argon2id, session tests | Email verification and password reset are deferred. |
| F02 profile/session | IMPLEMENTED | `/users/me`, expiry/revocation, HttpOnly cookie tests | Production TLS topology remains to validate. |
| F03 catalogue | IMPLEMENTED | PostgreSQL products, idempotent seed, `/billing/products` | Stripe identifiers remain unset. |
| F06 wallet/ledger | IMPLEMENTED | Atomic wallet service, immutable entries, row locks, concurrency tests | Paid credit workflows are deferred to Phase 3. |
| F12 admin access | PARTIAL | Server-side role dependency and denied regular-user test | Moderation persistence/workflows are deferred. |
| S01 password/session security | IMPLEMENTED | Argon2id, token hashes, expiry, revocation, rotation | Email/password recovery is deferred. |
| S02 CSRF/RBAC/ownership | IMPLEMENTED | CSRF bootstrap, origin checks, admin dependency, session-derived wallet ownership | Production CSP and distributed deployment remain. |
| S06 abuse protection | PARTIAL | Process-local auth sliding window | Shared rate limiting is required for multiple instances. |
| DB migrations | IMPLEMENTED | Alembic upgrade, downgrade, upgrade against PostgreSQL | No automatic schema creation in the application. |
| Local infrastructure | IMPLEMENTED | Project-specific Compose network, volume, healthchecks, non-root backend | Production orchestration is out of scope. |
| Stripe/AI | DEFERRED | Explicit `integration_pending` payment boundary | Phase 3/4. |
| Frontend API mode | IMPLEMENTED | CSRF bootstrap/rotation in `HttpApiClient`, real browser journey | Mock mode remains independent. |

## Evidence

- Backend unit and PostgreSQL integration tests: `backend/tests/`.
- Real frontend API-mode journey: `frontend/tests/e2e/backend_journey.py`.
- Frontend Phase 1.1 evidence: `frontend/docs/audit/TRACEABILITY_MATRIX.md` and its historical reports.
