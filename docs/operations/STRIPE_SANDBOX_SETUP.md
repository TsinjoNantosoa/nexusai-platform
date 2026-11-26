# Stripe Sandbox setup

This procedure is for the temporary Stripe Sandbox only. It prepares configuration for Phase 3.1; it does not create products, prices, Checkout Sessions, subscriptions, refunds, or webhook business logic.

## Safety rules

- Never paste a Stripe key into Codex, a commit, an issue, a chat, a frontend variable, or a command containing the literal value.
- Keep the key in the WSL2 process environment only for the shortest required session. Do not create `.env` files for the key.
- Stripe test and restricted keys are server-side credentials. The documented prefixes are `sk_test_` and `rk_test_`; live prefixes are rejected by application configuration.
- The owner-requested `rkcs_test_` format is accepted for compatibility but is not confirmed by the official documentation reviewed for this phase. Verify it with the owner’s Sandbox output before use.
- Do not run `stripe listen` until Phase 3.1 adds and tests a webhook endpoint.
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

The following reads secrets interactively and never places their values in shell history. Run only in the owner’s WSL2 session, and unset them when finished. The webhook secret should remain unset until an approved Phase 3.1 endpoint and forwarding session exist.

```bash
cd /mnt/c/Users/Tsinjo/Documents/projet/nexusai-stripe
read -r -s -p 'Stripe Sandbox API key: ' NEXUSAI_STRIPE_SECRET_KEY
printf '\n'
export NEXUSAI_STRIPE_ENABLED=false
export NEXUSAI_STRIPE_API_VERSION=2026-11-18.endive
export NEXUSAI_FRONTEND_BASE_URL=http://127.0.0.1:5173
export API_PROXY_TARGET=http://127.0.0.1:8100
```

Keep `NEXUSAI_STRIPE_ENABLED=false` for Phase 3.0. When Phase 3.1 has an approved webhook endpoint and the owner has obtained its Sandbox signing secret, enable the integration in the same private session:

```bash
read -r -s -p 'Stripe Sandbox webhook signing secret: ' NEXUSAI_STRIPE_WEBHOOK_SECRET
printf '\n'
export NEXUSAI_STRIPE_ENABLED=true
docker compose --project-name nexusai-phase3-stripe up -d --build
```

The application fails closed if enabled without both secrets. Do not run `docker compose config` after entering secrets because rendered configuration can display environment values. When finished:

```bash
unset NEXUSAI_STRIPE_SECRET_KEY NEXUSAI_STRIPE_WEBHOOK_SECRET
unset NEXUSAI_STRIPE_ENABLED NEXUSAI_STRIPE_API_VERSION NEXUSAI_FRONTEND_BASE_URL API_PROXY_TARGET
```

## Verification without exposing secrets

Use configuration tests and health checks; do not print environment variables:

```bash
cd /mnt/c/Users/Tsinjo/Documents/projet/nexusai-stripe/backend
python -m pytest tests/test_security_unit.py -q
curl --fail http://127.0.0.1:8100/health/live
curl --fail http://127.0.0.1:8100/health/ready
```

Stripe CLI authentication and product listing may be verified by the owner in the Sandbox session, but no product creation belongs to Phase 3.0. A future webhook forwarding command must target the approved Phase 3.1 route and must retain the CLI-generated signing secret only in the owner’s secure environment.

## Recovery and expiry

The temporary Sandbox expires after seven days according to the owner’s setup context. Treat all test product, price, customer, and event identifiers as disposable. Before expiry, record only non-secret configuration metadata and recreate the Sandbox deliberately; never commit or export the key.
