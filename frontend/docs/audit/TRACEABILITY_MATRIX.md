# NexusAI traceability matrix — Phase 1.1

Date: 2026-11-25

This matrix reflects the current implementation. The authoritative requirements remain in `docs/CAHIER_DES_CHARGES.md` and are unchanged.

## Status vocabulary

- **IMPLEMENTED**: demonstrated by source and automated evidence.
- **PARTIAL**: frontend behavior exists, but an external or production boundary remains.
- **MOCK ONLY**: intentionally simulated in the frontend service.
- **BACKEND REQUIRED**: cannot be proven by this repository.
- **NOT TESTED**: no evidence claimed.

## Functional requirements

| ID | Status | Evidence and remaining boundary |
| --- | --- | --- |
| F01 Auth | PARTIAL / MOCK ONLY | Demo login, registration, validation, and logout are tested; real sessions and email remain FastAPI work. |
| F02 Profile/session | PARTIAL | Query/session guards and in-memory mock state exist; secure cookie rotation and revocation require FastAPI. |
| F03 Catalogue | PARTIAL | Mock catalogue and API adapter exist; server-authoritative catalogue and prices require FastAPI. |
| F04 Checkout/return | PARTIAL / MOCK ONLY | Success, pending, declined, duplicate, and canceled scenarios are tested; Stripe/webhooks remain external. |
| F05 Premium/portal | PARTIAL / MOCK ONLY | Mock renewal/failure/cancel rules exist; Customer Portal and invoices require Stripe/backend. |
| F06 Wallet/ledger | PARTIAL / MOCK ONLY | Mock append-only ledger and responsive wallet are tested; persistence/concurrency require PostgreSQL. |
| F07 Characters | IMPLEMENTED / PARTIAL | Four local WebP portraits and responsive routes are verified; redistribution rights remain unverified. |
| F08 Conversations | PARTIAL / MOCK ONLY | Mock chat, SSE parser, cancellation, and error states are tested; provider/persistence require backend. |
| F09 Memory/affinity | MOCK ONLY | Mock controls exist; server-owned memory and affinity contracts remain open. |
| F10 Reservation/refund | MOCK ONLY | Two-gem reservation and terminal restitution are tested; atomic reconciliation requires backend. |
| F11 PWA | PARTIAL | Manifest, icons, offline fallback, prompt updates, protected operations, and 48-entry build are verified; physical installation is not tested. |
| F12 Admin/moderation | PARTIAL / MOCK ONLY | Admin guard and mock reports are tested; RBAC and moderation require FastAPI. |
| F13 Export/deletion | NOT TESTED / BACKEND REQUIRED | UI boundary exists; approved endpoints and retention policy are absent. |
| F14 Community | NOT TESTED | V2/out of scope. |

## Financial and security requirements

| ID | Status | Evidence and remaining boundary |
| --- | --- | --- |
| R01–R08 | MOCK ONLY / BACKEND REQUIRED | Mock balance, ledger, idempotency, duplicate protection, reservation, restitution, and review states are covered; server authority and concurrency are not. |
| S01 | PARTIAL | No app session data is written to browser storage; HttpOnly cookies and rotation require backend. |
| S02 | PARTIAL | In-memory CSRF header preparation and admin UX guard exist; server CSRF/RBAC enforcement requires FastAPI. |
| S03 | IMPLEMENTED for current frontend | No secrets found; root and frontend ignore rules protect future environment files. Runtime secret injection remains backend/deployment work. |
| S04 | PARTIAL | UI/mock validation exists; server payload validation and sanitization require FastAPI. |
| S05 | PARTIAL | No webhook call originates in the UI; Stripe signature and ledger verification require backend. |
| S06 | PARTIAL | Offline and UX guards exist; rate limiting and cost ceilings require backend. |
| S07 | NOT TESTED / BACKEND REQUIRED | Containers, TLS, database network, CI, and supply-chain policy remain release work. |
| S08 | IMPLEMENTED for configured PWA | API/private routes are excluded from runtime caching; production hosting must preserve the same policy. |

## Responsive and PWA evidence

| Area | Status | Evidence |
| --- | --- | --- |
| Mobile navigation | IMPLEMENTED | Accessible menu, Escape/focus trap, close-on-navigation, 44px controls, and backdrop isolation in `Shell.tsx`. |
| Narrow layout | IMPLEMENTED | Matrix covers 280, 320, 360, 375, 390, 414px with zero measured document/body overflow. |
| Tablet/desktop layout | IMPLEMENTED | Matrix covers 768, 1024, 1440, and 1920px with zero measured overflow. |
| Auth autofill | IMPLEMENTED | Dark-theme autofill styling added without populating credentials. |
| PWA cache | IMPLEMENTED / PARTIAL | 48 entries include four public portraits; no API/private response cache; physical Android/iOS installation not tested. |

## Acceptance tests

| Test set | Status |
| --- | --- |
| Vitest baseline | IMPLEMENTED — 37 tests pass; existing assertions retained. |
| Existing Chromium journeys | IMPLEMENTED — financial and chat journeys pass. |
| Responsive Chromium matrix | IMPLEMENTED — 10 viewports × 13 routes, no page errors or overflow offenders. |
| FastAPI/PostgreSQL/Stripe/AI tests | NOT TESTED — no backend or provider is present. |
| Physical PWA installation | NOT TESTED — no Android/iOS device was used. |

## Open risks

- Character redistribution/licensing rights remain unverified.
- `bun audit` reports two moderate transitive build/development advisories.
- Real authentication, CSRF enforcement, RBAC, payments, ledger concurrency, AI persistence, and production hosting remain backend work.

