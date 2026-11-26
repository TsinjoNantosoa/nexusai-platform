# Phase 2.1 security report

## Authentication and request security

- Expired and revoked sessions return 401 and cannot be reused for account or wallet access.
- Missing, empty, invalid, cross-session, and revoked-session CSRF tokens return 403 without mutating state.
- Disallowed state-changing origins return 403; allowed-origin and trusted-host lists are explicit.
- User A cannot read or modify User B's wallet through exposed routes or client-supplied identifiers.
- Invalid authentication attempts return 429 at the configured threshold, recover after the deterministic window, remain separated by user key, and cannot bypass the limiter with `X-Forwarded-For`.
- The limiter is process-local and must be replaced or fronted by shared storage before multi-worker deployment.

## Financial integrity

- Welcome wallet creation is unique and replay-safe.
- Internal credits are service-only, atomic, integer-valued, reference-idempotent, and reject contradictory retries.
- PostgreSQL row locks serialize spending and refunds; refunds are bounded by the original debit.
- Duplicate, excessive, partial, concurrent, cross-wallet, and failed operations preserve `wallet.balance == SUM(wallet_entries.amount)` and non-negative balances.

## Production configuration

Production requires `NEXUSAI_ENVIRONMENT=production`, `NEXUSAI_COOKIE_SECURE=true`, explicit HTTPS `NEXUSAI_ALLOWED_ORIGINS`, and explicit `NEXUSAI_TRUSTED_HOSTS`. Startup rejects wildcard origins, HTTP origins, wildcard trusted hosts, invalid SameSite values, non-positive session lifetime, and non-positive limiter settings. Credentialed CORS is never configured with `*`; arbitrary forwarded headers are not trusted.

These checks do not establish TLS termination, CSP, reverse-proxy hardening, distributed rate limiting, secret management, backup/restore, or public deployment security.

## Dependency findings

| Scope | Previous package | Corrected package | Finding | Result |
| --- | --- | --- | --- | --- |
| Runtime | `python-dotenv==1.0.1` | `python-dotenv==1.2.4` | `PYSEC-2026-2270` | No finding in validated environment |
| Runtime/transitive | `starlette==0.41.3` via FastAPI | `starlette==1.10.0`, FastAPI `0.165.0` | `PYSEC-2026-161`, `1941`, `1942`, `2280`, `2281`, `248`, `249` | No finding in validated environment |
| Development | `pytest==8.3.4` | `pytest==9.2.0` | `PYSEC-2026-1845` | No finding in validated environment |
| Development | absent | `pip-audit==2.10.1` | Audit tooling | Development extra only; not in the production image |

`pip-audit --local` also reports the editable local package as not published to PyPI; that is a scanner skip reason, not a vulnerability. No known vulnerabilities were reported for the installed dependencies after the targeted corrections.

## Frontend residuals

`bun audit` reports `GHSA-3g3m-2fjr-6pw4` for `glob@11.1.0` through `vite-plugin-pwa > workbox-build`, and `GHSA-g3hv-75wg-m249` for `minimatch` paths through ESLint, TypeScript ESLint, and Workbox. The current Workbox dependency requires the affected major range; no compatible targeted fix was applied, and no override was used. These are build/development dependency exposures, not claimed runtime authorization controls. Future remediation should upgrade the Vite-PWA/Workbox architecture together and rerun all frontend/PWA validation.
