# NexusAI contribution rules

## Architecture

- This directory is an independent React 19, TypeScript strict, Vite SPA.
- TanStack Router remains file-based and TanStack Query owns client data state.
- The future backend is Python/FastAPI/PostgreSQL under the same-origin `/api/v1` prefix.
- Stripe Sandbox and an approved AI provider are backend responsibilities; the frontend never receives their secrets.
- Preserve the current NexusAI visual identity, French/English translations, routes, financial rules, and shadcn controls.
- Do not introduce Supabase, Firebase, Lovable Cloud, or a proprietary AI gateway.
- Do not modify `docs/CAHIER_DES_CHARGES.md`.

## Security and data

- Keep real secrets out of Git, `VITE_*` variables, browser storage, logs, and bundles.
- `.env.example` is safe to retain; all other environment files are ignored.
- Mock mode is an explicit demonstration only. API mode must never fall back to mock data after an HTTP failure.
- Do not cache authenticated API responses, conversations, profiles, wallet, billing, webhook, or payment-verification data in the PWA.
- Never replay financial or paid AI requests automatically after reconnection.

## Validation

- Use Bun and `bun.lock`; prefer `bun install --frozen-lockfile`.
- Before committing, run lint, typecheck, Vitest, build, and available Chromium journeys.
- Do not disable tests, type checks, lint rules, or security scans to hide failures.
- Do not claim Stripe, PostgreSQL, FastAPI, or production-device validation from mock/frontend tests.

## Git safeguards

- Work on `feat/frontend-stabilization` or a more specific feature branch; never modify `main` directly.
- Preserve history and remotes. Use small local commits after successful validation.
- Never force-push, rewrite history, use `git reset --hard`, or run `git clean -fd`.
- Do not push, merge, deploy, or publish without explicit approval.
