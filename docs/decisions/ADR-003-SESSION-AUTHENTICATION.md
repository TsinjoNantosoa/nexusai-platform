# ADR-003: opaque cookie sessions with CSRF

Date: 2026-11-25
Status: Accepted for Phase 2

## Decision

Use random opaque session cookies with only token hashes stored in PostgreSQL. Use a separate session-associated CSRF token held in frontend memory and validated on all state-changing requests. Rotate both tokens after authentication and revoke sessions at logout or expiry.

## Consequences

The browser does not persist bearer tokens in local or session storage, and server-side revocation is possible. The CSRF bootstrap endpoint is compatible with the existing frontend client. Production HTTPS, cross-site deployment, email verification, password reset, and distributed rate limiting remain release decisions.
