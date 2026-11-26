# NexusAI security policy

## Reporting

Do not open a public issue containing a vulnerability, credential, private user data, or payment information. Report privately to the project owner with reproduction steps and affected commit.

## Local safeguards

- Root and frontend ignore rules protect environment files, keys, certificates, dependencies, build output, logs, databases, and browser artifacts.
- Passwords use Argon2id; raw passwords and session tokens are never logged or persisted.
- Session cookies are HttpOnly with configurable Secure and SameSite attributes.
- Session token hashes and CSRF token hashes are stored in PostgreSQL; the frontend keeps the active CSRF token only in memory.
- State-changing requests require CSRF validation and allowed-origin checks.
- Authentication has a process-local sliding-window limiter. A shared limiter is required before multi-instance deployment.
- Financial movements use integer gem amounts, PostgreSQL row locks, unique operation references, and a non-negative balance constraint.
- Production configuration rejects insecure cookies, wildcard or HTTP origins, wildcard trusted hosts, invalid SameSite values, and non-positive session/rate-limit settings.
- Destructive database operations require an explicitly authorized disposable test URL, database name, role, and effective PostgreSQL identity. Development and production targets are rejected before destructive SQL executes.
- Backend dependency auditing is reproducible with the pinned development-only `pip-audit==2.10.1`; the validated backend environment reports no known vulnerabilities.
- Stripe is Sandbox-only: Stripe is disabled by default, server secrets use `SecretStr`, live and unknown key formats are rejected, and enabling Sandbox mode requires both API and webhook secrets. Checkout is server-authoritative, uses hosted Stripe pages, account-scoped mappings, CSRF, rate limiting, durable idempotency and ownership checks. No Stripe secret is accepted in frontend configuration.
- Development, disposable integration-test, and future production database identities are separated by Compose service, network, volume, database, and role. Backup and recovery procedures are documented in `docs/operations/DATABASE_BACKUP_RESTORE.md`.

## Known limitations

This phase does not provide production TLS/CSP configuration, email verification, password reset, external rate-limit storage, Stripe signature verification, wallet fulfillment, subscriptions, refunds, AI-provider controls, an executed backup/restore test, or a GDPR/PCI certification claim. The temporary Stripe Sandbox is not production and expires after seven days according to the owner’s setup context. The Phase 2.1 local database incident is documented in `docs/audit/INCIDENT_001_DATABASE_ISOLATION.md`; no recovery artifact was found and no claim of data recovery is made. The frontend retains two documented moderate transitive build/development advisories and recovered artwork licensing remains unverified.

Never use real credentials or real customer data in the local Compose database.
