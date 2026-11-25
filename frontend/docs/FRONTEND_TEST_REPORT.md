# Frontend test report

Date: 2026-11-25

## Phase 1 execution

- Vitest: 5 files, 37 tests passed.
- ESLint: passed with 10 pre-existing `react-refresh/only-export-components` warnings.
- TypeScript build check: passed with `bunx --bun tsgo -b --noEmit`.
- Vite production build: passed with generated `dist/sw.js` and 44 precache entries.
- Financial Chromium journey: passed purchase, duplicate, responsive, and browser-error checks.
- Chat Chromium journey: passed failure compensation, offline blocking, logout, storage, worker, and browser-error checks.

## Coverage notes

The journeys run in mock mode and do not validate FastAPI, PostgreSQL, Stripe, an AI provider, or production devices. They verify that private data is not written by the app to browser storage and that no service worker is registered during development.

The documented `bun run lint`, `bun run typecheck`, `bun run test`, and `bun run build` commands pass. The package scripts use explicit Bun/Node entrypoints for Windows portability.
