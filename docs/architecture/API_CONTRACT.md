# Phase 2 API contract

The frontend uses same-origin `/api/v1` with `credentials: include`. Errors have the shape `{code, request_id, message}` and use the documented 401, 403, 404, 409, 422, 429, 501, and 503 classes.

Implemented endpoints:

- `GET /health/live`, `GET /health/ready`
- `GET /api/v1/auth/csrf`, `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`
- `GET /api/v1/users/me`
- `GET /api/v1/wallet`, `GET /api/v1/wallet/transactions?limit=&offset=`
- `GET /api/v1/billing/products`, `GET /api/v1/billing/subscription`
- `GET /api/v1/admin/reports` for administrators; current report data is empty until moderation is implemented.

`POST /api/v1/billing/checkout` and `POST /api/v1/billing/portal` return `integration_pending` with 501. No price, gem credit, Stripe identifier, or payment confirmation is fabricated. The existing frontend `HttpApiClient` bootstraps CSRF and captures rotated `X-CSRF-Token` response headers.
