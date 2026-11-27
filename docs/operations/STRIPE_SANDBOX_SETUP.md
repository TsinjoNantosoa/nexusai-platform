# Stripe Sandbox setup

This procedure is for the temporary Stripe Sandbox only. Phase 3.1 provides the product/price catalogue, Phase 3.2 adds hosted one-time Checkout for Starter/Plus, and Phase 3.3 adds signed webhook intake plus verified one-time fulfillment. It does not create subscriptions, renew invoices, or process refunds.

## Safety rules

- Never paste a Stripe key into Codex, a commit, an issue, a chat, a frontend variable, or a command containing the literal value.
- Keep the key in the WSL2 process environment only for the shortest required session. Do not create `.env` files for the key.
- Stripe test and restricted keys are server-side credentials. The documented prefixes are `sk_test_` and `rk_test_`; live prefixes are rejected by application configuration.
- The owner-requested `rkcs_test_` format is accepted for compatibility but is not confirmed by the official documentation reviewed for this phase. Verify it with the owner’s Sandbox output before use.
- Do not run `stripe listen` until a tested webhook endpoint is approved.
- Do not disable Windows Smart App Control or other Windows security policies.

## Project-isolated Compose

From Ubuntu WSL2, use the new worktree and project name. These commands use ports and volumes that are distinct from Phase 2:

```bash
cd /mnt/c/Users/Tsinjo/Documents/projet/nexusai-stripe
docker compose --project-name nexusai-phase3-stripe config --quiet
docker compose --project-name nexusai-phase3-stripe --profile test up -d postgres-test
```

The disposable integration URL is the test service on port `56433`; the project development database, if the owner explicitly starts it, is on port `56432`. Do not use the older `nexusai_phase2_postgres` volume or ports `55432`/`55433`.

## Secure environment handoff

The following reads secrets interactively and never places their values in shell history. Run only in the owner’s WSL2 session, and unset them when finished. The webhook secret may remain unset for catalogue work; it is still required whenever the application is enabled because webhook processing is not implemented here.

```bash
cd /mnt/c/Users/Tsinjo/Documents/projet/nexusai-stripe
read -r -s -p 'Stripe Sandbox API key: ' NEXUSAI_STRIPE_SECRET_KEY
printf '\n'
export NEXUSAI_STRIPE_ENABLED=false
export NEXUSAI_STRIPE_API_VERSION=2026-11-18.endive
export NEXUSAI_FRONTEND_BASE_URL=http://127.0.0.1:5173
export API_PROXY_TARGET=http://127.0.0.1:8100
```

The standard Compose file ignores `NEXUSAI_STRIPE_ENABLED` and owner credential variables. Stripe remains disabled unless the guarded `tools/start_stripe_demo.ps1 -OwnerApproved` launcher supplies private `NEXUSAI_STRIPE_DEMO_*` variables, including the non-secret account ID. The application fails closed if enabled without both configured secrets. Do not run `docker compose config` after entering secrets because rendered configuration can display environment values.

When finished:

```bash
unset NEXUSAI_STRIPE_SECRET_KEY NEXUSAI_STRIPE_WEBHOOK_SECRET
unset NEXUSAI_STRIPE_DEMO_ENABLED NEXUSAI_STRIPE_DEMO_SECRET_KEY NEXUSAI_STRIPE_DEMO_WEBHOOK_SECRET
unset NEXUSAI_STRIPE_ENABLED NEXUSAI_STRIPE_API_VERSION NEXUSAI_FRONTEND_BASE_URL API_PROXY_TARGET
```

## Owner catalogue procedure

After reviewing the dry-run, the owner may run the following commands without sharing credentials with Codex:

```bash
cd /mnt/c/Users/Tsinjo/Documents/projet/nexusai-stripe
docker compose --project-name nexusai-phase3-stripe up -d --build
docker compose --project-name nexusai-phase3-stripe exec backend python -m alembic upgrade head
docker compose --project-name nexusai-phase3-stripe exec backend python -m app.billing.bootstrap --dry-run
docker compose --project-name nexusai-phase3-stripe exec backend python -m app.billing.bootstrap --apply
docker compose --project-name nexusai-phase3-stripe exec backend python -m app.billing.bootstrap --verify
docker compose --project-name nexusai-phase3-stripe exec backend python -m app.billing.bootstrap --apply
```

The final repeat should reuse all three products and prices. Inspect the Sandbox separately; never treat a local success message as proof of an owner-verified remote catalogue.

## Verification without exposing secrets

Use configuration tests and health checks; do not print environment variables:

```bash
cd /mnt/c/Users/Tsinjo/Documents/projet/nexusai-stripe/backend
python -m pytest tests/test_security_unit.py -q
curl --fail http://127.0.0.1:8100/health/live
curl --fail http://127.0.0.1:8100/health/ready
```

## Recovery and expiry

The temporary Sandbox expires after seven days according to the owner’s setup context. Treat all test product, price, customer, and event identifiers as disposable. Before expiry, record only non-secret configuration metadata and recreate the Sandbox deliberately; never commit or export the key.

When the temporary Sandbox expires, create a new private key, confirm the new account identity, keep the old account mappings for history, and rerun `--dry-run`, `--apply`, `--verify`, and a second `--apply`. The account-scoped mapping table prevents IDs from the expired account from being treated as valid in the replacement account.
