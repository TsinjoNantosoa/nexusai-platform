# NexusAI — requirements mapping and implementation plan

## Prerequisites

1. **The complete Cahier des charges V1.0 has now been supplied and read.** It is preserved unchanged in `docs/CAHIER_DES_CHARGES.md`. The exact IDs F01–F14, R01–R08, W01–W06, S01–S08 and T01–T18 are mapped in `docs/FRONTEND_IMPLEMENTATION_STATUS.md`.
2. **This Lovable project uses TanStack Start and TanStack Router.** React Router cannot replace its routing system. Approval is needed to adapt navigation while retaining React, TypeScript, Vite, the requested page URLs, and the external FastAPI architecture. No production backend will be created here.

## What the archive contains

React 18/Vite 5/Tailwind 3 source with React Router, TanStack Query, React Hook Form, Zod, i18next and Lucide. French and English translations exist. Authentication, pricing, wallet and billing-return screens are partially implemented. Character discovery, character profiles, conversations, chat, settings and administration are explicit placeholders. No production database, user export, character images, PWA manifest or service worker is included. The authoritative specification was supplied separately after archive inspection.

The archive lists an unused Supabase dependency, but the inspected application uses an in-memory mock client or the configured external HTTP API. No connected database migration is necessary or authorized.

## Preliminary mapping

| Brief area | Existing source | Planned work | Dependency |
| --- | --- | --- | --- |
| FE-00: foundation | Shell, translations, API interface | Semantic dark design system; adapt all 13 route patterns; session/query boundaries; structured errors | Routing approval; F01–F03, S01–S04 |
| FE-01: financial demo | Auth, pricing, wallet, partial billing | Fix login/cache issues; deterministic 20-gem onboarding; exact product offers; explicit simulated success/pending/decline/duplicate flows; subscription and portal interface | F01–F06, R01–R04/R08; real billing requires FastAPI |
| FE-02: conversations | Placeholders | Atlas, Luna, Nova, Echo; discovery, profiles, history, streaming, memory, affinity, 2-gem charge and restitution, 2,000-character limit | F07–F10, R05–R07; real AI requires FastAPI |
| FE-03: PWA and settings | Placeholders | Manifest/icons; controlled public-shell offline support; offline action blocking; updates; installation information; account settings | F11/F13, W01–W06, S08; private operations require approved endpoints |
| FE-04: moderation/admin | Placeholder and staff guard | Anonymized demo reports, catalogue, moderation, audit and webhook overview; explicit pending actions | Backend authorization and missing contracts |
| FE-05: handover | Two source test files | Rule tests, route and browser journeys, 360/768/1440 layout checks, architecture/API/status/test/handover documents | Milestone implementation |

The detailed matrix separately records every specification ID, its frontend scope, backend dependency and current verification status. F14 is V2/P2 and remains outside V0.1/V1.0.

## Important defects found by source inspection

- Admin demonstration login is rejected by the mock API despite an admin branch in mock state.
- Checkout performs a full-page redirect that discards in-memory login and order state.
- The mock order initializer reads its own `order` variable before initialization.
- Return-page confirmation cannot advance a newly pending mock order to paid; its confirmation branch is only entered after the order is already paid.
- Login does not refresh the cached session query.
- Demo login seeds 140 gems and describes Plus as a renewable subscription, inconsistent with the requested initial 20 gems and one-time Plus pack.
- API cancellation/profile operations use contracts not listed as finalized in the brief.

These are inspection findings, not executed test results.

## Implementation sequence

1. Completed: read the supplied specification in full, preserve it as `docs/CAHIER_DES_CHARGES.md`, and map every requirement and acceptance-test ID. Obtain routing approval before adapting application code.
2. Deliver and verify FE-00 and FE-01 first. Preserve the explicitly simulated banner, prohibit real payments, and keep prices/backend-authoritative data separate from mock state.
3. Deliver FE-02, FE-03 and FE-04 sequentially, checking each milestone before continuing.
4. Run applicable automated tests and browser journeys; document actual results and unverified integrations. Complete the requested handover documentation.

## Technical approach

- Keep this project's pinned TanStack packages and bootstrap; do not import the source App.tsx/BrowserRouter as a second router.
- Preserve `/`, `/login`, `/register`, `/explore`, `/characters/:id`, `/conversations`, `/chat/:id`, `/wallet`, `/pricing`, `/billing/success`, `/billing/cancel`, `/settings`, `/admin`.
- Separate typed API contracts, HTTP transport and deterministic in-memory demonstration services. UI uses typed hooks, not direct financial state mutation.
- Preserve external FastAPI cookie authentication with `credentials: include`; CSRF remains an explicit integration contract. Never persist passwords, sessions, private conversations or private query caches.
- Use guarded vite-plugin-pwa registration only for published offline support; exclude private data and billing/auth routes from caching. Preview must not register an app-shell worker.
- No Cloud, production authentication service, database, real Stripe/AI integration, paid service or publishing is included.

## Current verification status

Archive inspection and complete specification review are finished without executing imported source or scripts. No source tests or application journeys have run. The preview remains unchanged while routing approval is pending. Real Stripe, PostgreSQL, server security and infrastructure acceptance tests remain external responsibilities, not validations obtainable from frontend mocks.