# Authentication and sessions

Registration creates a user, wallet, and 20-gem welcome entry in one database transaction. Registered users receive the ordinary `user` role.

Login and registration require a CSRF token obtained from `GET /api/v1/auth/csrf`. The endpoint returns a token and sets a readable CSRF cookie. After authentication, the backend rotates both the opaque session token and the CSRF token. Only the session token is HttpOnly; the frontend stores the active CSRF value in memory and sends `X-CSRF-Token` on mutations.

The database stores SHA-256 hashes of session and CSRF tokens, session expiry, revocation time, and last-seen time. Logout revokes the session and clears both cookies. Passwords use Argon2id. Authentication failures are generic and authentication attempts are rate-limited per process.

Allowed origins and trusted hosts are explicit. The development cookie configuration is `Secure=false`, `SameSite=Lax`; HTTPS deployments must set `Secure=true` and use explicit HTTPS origins. Production startup rejects wildcard origins, HTTP origins, wildcard trusted hosts, non-positive session or limiter settings, and unsupported SameSite values. `SameSite=None` also requires Secure cookies.

Required production variables are:

```text
NEXUSAI_ENVIRONMENT=production
NEXUSAI_COOKIE_SECURE=true
NEXUSAI_ALLOWED_ORIGINS=https://app.example.test
NEXUSAI_TRUSTED_HOSTS=app.example.test,api.example.test
```

The application does not enable arbitrary forwarded-header trust; reverse-proxy TLS and host forwarding must be explicitly configured and constrained by the deployment architecture. Rate limiting remains process-local.
