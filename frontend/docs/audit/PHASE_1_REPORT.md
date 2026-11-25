# Phase 1 implementation report

Date: 2026-11-25
Branch: `feat/frontend-stabilization`

## Scope

Phase 1 migrates the existing frontend to a portable Vite SPA without changing the public route URLs, translation surface, financial mock rules, or backend handover boundary.

## Delivered

- Replaced TanStack Start/Nitro/Lovable build wiring with standard Vite, React, TanStack Router, and `index.html` entry points.
- Preserved the generated file-based route tree and browser journeys.
- Added strict `VITE_DATA_MODE=mock|api` validation; invalid values fail configuration and API errors never fall back to mock data.
- Added same-origin API proxying, credentialed requests, in-memory CSRF token support, fragmented SSE parsing, and no browser persistence for sessions or private data.
- Recovered four character WebP files into `public/assets/characters/` and changed runtime descriptors to local paths.
- Generated a production PWA worker with public-only caching, prompt updates, and explicit localhost opt-in through `?sw=on`.
- Added wallet, checkout, and billing-operation markers so a waiting worker cannot interrupt critical operations.
- Replaced the Lovable runtime error hook with a local console error reporter and removed obsolete server entry files.

## Phase 0 findings resolved

| Finding | Phase 1 result |
| --- | --- |
| AUD-01 missing character pixels | Four local WebP assets recovered and referenced at runtime. |
| AUD-02 platform/SSR coupling | Standard Vite SPA is the only runtime/build path. |
| AUD-03 dependency reproducibility | `bun.lock` retained; install remains Bun-first and frozen-lockfile compatible. |
| AUD-04 dependency advisories | Targeted audit completed; two moderate transitive advisories remain and are documented in the security report. |
| AUD-05 secret/config hygiene | Ignore rules expanded; tracked-secret scan found no credential markers. |
| AUD-06 unsafe local worker activation | Localhost requires production preview plus `?sw=on`; development never registers. |
| AUD-07 worker update interruption | Prompt/deferred activation and active-operation guards added. |
| AUD-08 SSR request isolation risk | SSR removed; browser API calls use same-origin proxy and credentials. |
| AUD-09 CSRF contract gap | Client header support and backend contract proposal documented; server implementation remains pending. |
| AUD-10 permissive data mode | Only `mock` and `api` are accepted, with no fallback. |
| AUD-11 documentation drift | Architecture, README, handover, and API contract updated. |
| AUD-12 telemetry/instructions coupling | Runtime telemetry integration removed; historical audit references remain intentionally as evidence. |

## Not in scope

There is no FastAPI, PostgreSQL, Stripe Sandbox, AI provider, production hosting, or real-device validation in this repository. Those remain Phase 2/backend or release work.
