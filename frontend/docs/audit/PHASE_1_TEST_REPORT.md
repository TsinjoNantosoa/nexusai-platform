# Phase 1 test report

Date: 2026-11-25

## Automated checks

| Check | Result |
| --- | --- |
| `bun run lint` | PASS; 10 pre-existing refresh warnings only. |
| `bun run typecheck` | PASS. |
| `bun run test` | PASS; 5 files, 37 tests. |
| `bun run build` | PASS; production worker generated with 44 precache entries. |
| `bun install --frozen-lockfile` | PASS during Phase 1 install verification. |
| `python tests/e2e/financial_journey.py` | PASS; purchase, duplicate, responsive, and browser-error checks. |
| `python tests/e2e/chat_journey.py` | PASS; chat failure, offline, logout, storage, worker, and browser-error checks. |

## Runtime coverage

- Mock login, catalogue, wallet, pricing, checkout scenarios, chat, refund behavior, offline blocking, and logout were exercised in Chromium.
- The four character cards loaded through local assets in the independently built SPA.
- API-mode integration with a real FastAPI server was not claimed because no backend is present.
- The package scripts use explicit Bun/Node entrypoints so the documented commands work on this Windows environment.

## Release checks still required

- Serve the production `dist` directory behind a real SPA fallback and verify all direct route refreshes.
- Validate the proposed CSRF/session contract against FastAPI.
- Run Stripe Sandbox, PostgreSQL, AI-provider, security-server, and real-device acceptance suites.
