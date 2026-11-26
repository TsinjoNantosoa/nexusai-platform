# Phase 3.2.1 — Runtime Validation

## Git and environment

- Branch: `feat/stripe-integration`.
- Remote: existing `origin` preserved; no remote command was executed.
- Baseline: `7de8dfa`; pre-review local Phase 3.2 commits remain intact.
- Working tree was clean before this review; final review must include the two local audit changes and the customer-binding fix only.
- Compose syntax check passed with `docker compose --project-name nexusai-phase3-stripe --profile test config --quiet`.
- Development identity: database `nexusai`, role `nexusai`.
- Test identity: database `nexusai_test`, role `nexusai_test`.
- Disk space was sufficient for the build; no volume deletion or prune operation was used.

## Backend and PostgreSQL

| Command/check | Result |
| --- | --- |
| `ruff check app migrations tests` | PASS |
| Full backend Pytest | PASS — `70 passed`, 1 existing Starlette/httpx warning |
| `pip-audit --local` | PASS — no known vulnerabilities |
| Disposable migration upgrade/rollback coverage | PASS on the isolated test target |
| Development migration | `0003_checkout_orders` |
| `/health/live` | `200`, `{"status":"ok"}` |
| `/health/ready` | `200`, `{"status":"ready"}` |
| Backend rebuild | PASS after the initial network/download timeout; image rebuilt successfully |

Read-only PostgreSQL checks confirmed the three existing catalogue mappings,
the `orders` and `stripe_customer_mappings` constraints/foreign keys, and
wallet/ledger tables. No destructive operation was run against development.

The backend was left healthy with Stripe explicitly disabled after the
containment step. The development database contains one review order from the
initial accidental Sandbox request; it is pending/unpaid/unfulfilled and has
no purchase ledger entry.

## Frontend

| Command/check | Result |
| --- | --- |
| `bun run lint` | PASS, 10 existing Fast Refresh warnings |
| `bun run typecheck` | PASS |
| `bun run test` | PASS — `37 tests` |
| `bun run build` | PASS — 48 PWA precache entries |
| `bun audit` | EXPECTED FAIL — 2 moderate transitive advisories documented above |

Headless Chromium was available through the system Playwright installation.
API-mode browser checks on configured port `5173` verified:

- Registration redirect to the authenticated wallet and pricing catalogue rendering.
- Starter and Plus visibility and Premium disabled in API mode.
- After Stripe disablement, a Starter checkout request returned `503`, stayed on the local origin, and did not fall back to mock mode.
- Unknown order status rendered safely and mobile pricing had no horizontal overflow.

The owner-Sandbox checkout path was not rerun after containment. Cancel-page and
language assertions were not treated as release evidence because the temporary
browser harness timed out during a focused rerun; code/build/test validation
still passed.

## Owner demonstration state

Local backend:

- `http://127.0.0.1:8100/health/live`
- `http://127.0.0.1:8100/health/ready`

Frontend should be started by the owner in the repository `frontend` directory
with API mode and the configured origin:

```powershell
$env:VITE_DATA_MODE="api"
$env:API_PROXY_TARGET="http://127.0.0.1:8100"
bun run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173/pricing`. Do not click a paid pack until the owner
has reviewed the accidentally created Sandbox Session and explicitly authorizes
the demonstration. No real card or payment was used by Codex.

## Final decisions

- Local runtime with Stripe disabled: **GO**.
- Checkout Sandbox without owner incident review: **NO-GO**.
- Owner Sandbox payment: **NO-GO pending explicit owner approval**.
- GitHub push: **NO-GO by policy**; owner-only operation.
- Phase 3.3: **NO-GO** until this review and the Sandbox incident are accepted.
