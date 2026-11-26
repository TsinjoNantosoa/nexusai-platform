# Phase 3.2 test report

## Executed results

| Command | Result |
| --- | --- |
| `backend/.venv/Scripts/ruff.exe check app migrations tests` | PASS |
| `pytest tests/test_checkout.py -q` | PASS — 6 tests |
| `pytest tests -q` | PASS — 69 tests |
| Disposable PostgreSQL migration upgrade to head | PASS — migration `0003_checkout_orders` |
| Disposable PostgreSQL migration rollback to `0002` and upgrade to `head` | PASS |
| `python -m pip_audit --local` | PASS — no known vulnerabilities; local package skipped because it is not on PyPI |
| `bun run lint` | PASS — 10 pre-existing Fast Refresh warnings |
| `bun run typecheck` | PASS |
| `bun run test` | PASS — 37 tests |
| `bun run build` | PASS — 48 PWA precache entries |
| Tracked secret-shaped credential scan | PASS — 0 credential-shaped tracked files |
| `docker compose ... config --quiet` | PASS |

The backend tests used the isolated `postgres-test` service at port `56433` and a fake Stripe gateway. No owner Sandbox credentials, real network calls, card details, or payment mutations were used.

## Covered controls

The new tests cover server-authoritative Starter pricing despite client fields, account-scoped Price selection, quantity one, Customer mapping, duplicate session reuse, conflicting idempotency, payment status without fulfillment, unchanged wallet balance, and live Checkout response rejection. Existing Phase 3.1 SDK normalization tests continue to pass.

## Not claimed

No end-to-end hosted payment is claimed. Responsive browser checks were not run in this phase. `bun audit` reports the two known moderate transitive `glob`/`minimatch` advisories; they were documented and not expanded in this phase. The owner’s final Sandbox validation remains outstanding.
