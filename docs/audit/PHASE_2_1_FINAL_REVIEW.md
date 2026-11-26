# Phase 2.1 final review

Date: 2026-11-26
Branch: `feat/backend-foundation`

## Acceptance result

The targeted authentication and wallet corrections pass against real PostgreSQL. The complete matrix below records 29 validated scenarios. Infrastructure and frontend entries include their exact command evidence and remaining boundaries; no physical device, production deployment, or external payment/AI claim is made.

## Decision summary

- Manual push to `feat/backend-foundation`: **CONDITIONAL GO** after owner review of the complete diff, local commits, dependency changes, residual Bun advisories, and secret scan.
- Pull request and merge into `main`: **CONDITIONAL GO** only after owner validation and manual publication; Codex did not merge or publish.
- Starting Phase 3 Stripe Sandbox: **CONDITIONAL GO** after owner accepts this phase and the documented sandbox-only boundaries; no Stripe code was added here.
- Public repository visibility: **NO-GO** until artwork redistribution rights and release supply-chain/security decisions are resolved.
- Public production deployment: **NO-GO**; TLS, CSP, distributed rate limiting, secret management, payments, AI, backups, and operational readiness remain unvalidated.

## Remaining risks

- The authentication limiter is process-local.
- Frontend `glob` and `minimatch` advisories remain in build/development dependency paths.
- Character artwork redistribution rights remain unresolved.
- Stripe, AI, email recovery, production TLS/CSP, external secrets, backups, CI policy, and physical PWA installation are not delivered.

## Validation incident

During local migration validation, the first downgrade was accidentally directed at the normal `nexusai` development database instead of the isolated `nexusai_test` database. The schema was immediately recreated and seeded, and no other Docker project or volume was touched; however, the prior local development records were not recoverable from this workspace. The final migration cycle used `nexusai_test`, and restart persistence was then verified on the recreated development database (`1` fictional user before restart and `1` after restart). This is an operational process failure and must be included in the owner's final review.

## Owner handoff commands

Manual local startup:

```powershell
docker compose up -d --build
Set-Location frontend
bun install --frozen-lockfile
$env:VITE_DATA_MODE = "api"
bun run dev -- --host 127.0.0.1 --port 5173
```

Review locally before publication:

```powershell
git status --short --branch
git log --oneline origin/main..HEAD
git diff --check origin/main...HEAD
git diff --stat origin/main...HEAD
git diff origin/main...HEAD
```

After the owner completes final validation, the owner may manually publish and open a review using their normal GitHub workflow. Codex must not run `git push`, create a pull request, or merge.
