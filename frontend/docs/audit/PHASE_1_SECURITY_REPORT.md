# Phase 1 security report

Date: 2026-11-25

## Repository and secret checks

- Existing Git history and `origin` were preserved; work is on `feat/frontend-stabilization`.
- Tracked-file scans for Stripe keys, AWS access-key markers, private-key blocks, and Lovable API key markers returned no matches.
- `.env`, local environment variants, key/certificate files, build output, coverage, and browser artifacts are ignored; `.env.example` remains allowed.
- No secret values were printed or added.

## Frontend controls

- API requests use `credentials: include` and the same-origin `/api/v1` boundary.
- CSRF values are held in memory and sent on mutations through `X-CSRF-Token`; bootstrap, rotation, and server verification remain backend contract work.
- `VITE_DATA_MODE` rejects unknown values and API failures are not converted into mock responses.
- The service worker excludes API, authentication, conversations, profiles, wallet, billing, checkout, webhook, and payment-verification data from caching.
- PWA activation is disabled in development and requires explicit opt-in on localhost production preview.
- Waiting worker activation is deferred while an element declares `data-operation-active="true"`.

## Dependency audit

`bun audit` reports two moderate transitive advisories:

- `glob` through `vite-plugin-pwa > workbox-build`.
- `minimatch` through the Workbox graph and development tooling.

No blind major upgrade was applied. The current versions are required by the selected Vite PWA/Workbox chain or development tool ranges; Phase 2 should reassess the chain before production release and apply a tested targeted fix.

## Residual risks

The backend must enforce HttpOnly session cookies, CSRF validation, authorization, idempotency, Stripe webhook verification, rate limits, and financial ledger invariants. Frontend tests cannot prove those properties.
