# Phase 2 security report

## Controls verified

- No production credentials, secrets, passwords, or raw session tokens are present in source or fixtures.
- Argon2id hashes passwords; session and CSRF token hashes are stored instead of raw tokens.
- HttpOnly session cookies, Secure configuration, SameSite configuration, expiry, revocation, and rotation are implemented.
- CSRF and allowed-origin validation protect state-changing requests.
- Regular users cannot access administrator routes; resource queries derive ownership from the authenticated session.
- Wallet mutations are internal services only and use PostgreSQL row locks, unique references, atomic transactions, and database balance constraints.
- Compose uses an isolated project network/volume, a non-root backend container, no PostgreSQL public wildcard binding, and no production credentials.
- Production settings fail closed when secure cookies, explicit HTTPS origins, or explicit trusted hosts are missing or unsafe. Credentialed CORS remains explicit and wildcard origins are rejected.
- `pip-audit==2.10.1` runs in the backend development extra and reports no known vulnerabilities after targeted version corrections.

## Limitations

The auth limiter is process-local and not suitable for multiple backend instances. TLS termination, CSP, email verification, password reset, audit-log event coverage, external secret management, Stripe webhook verification, AI-provider controls, and operational backup/restore remain release work. The two frontend transitive moderate build/development advisories and unverified artwork rights remain inherited limitations.
