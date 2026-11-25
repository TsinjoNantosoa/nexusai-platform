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

## Known limitations

This phase does not provide production TLS/CSP configuration, email verification, password reset, external rate-limit storage, Stripe signature verification, AI-provider controls, backup/restore, or a GDPR/PCI certification claim. The frontend retains two documented moderate transitive development/build advisories and recovered artwork licensing remains unverified.

Never use real credentials or real customer data in the local Compose database.
