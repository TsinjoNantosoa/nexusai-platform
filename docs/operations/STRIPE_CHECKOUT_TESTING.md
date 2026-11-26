# Stripe Checkout Sandbox testing

Codex tests use a fake gateway and the disposable PostgreSQL service. They do not use the owner’s Sandbox credentials or execute a payment. The owner must perform the final hosted Checkout validation manually.

## Local validation

```bash
cd /mnt/c/Users/Tsinjo/Documents/projet/nexusai-stripe
docker compose --project-name nexusai-phase3-stripe --profile test up -d postgres-test
cd backend
export NEXUSAI_TEST_DATABASE_URL='postgresql+psycopg://nexusai_test:nexusai_test@127.0.0.1:56433/nexusai_test'
export NEXUSAI_TEST_DATABASE_NAME=nexusai_test
export NEXUSAI_TEST_DATABASE_ROLE=nexusai_test
export NEXUSAI_TEST_DATABASE_DISPOSABLE=true
export NEXUSAI_DEVELOPMENT_DATABASE_URL='postgresql+psycopg://nexusai:nexusai@127.0.0.1:56432/nexusai'
python -m alembic upgrade head
python -m pytest tests/test_checkout.py -q
python -m pytest tests -q
```

## Owner runtime procedure

Supply private Sandbox variables interactively; never paste values into Codex, Git, logs, or frontend variables.

```bash
docker compose --project-name nexusai-phase3-stripe config --quiet
docker compose --project-name nexusai-phase3-stripe up -d --build
docker compose --project-name nexusai-phase3-stripe exec backend python -m alembic current
docker compose --project-name nexusai-phase3-stripe exec backend curl --fail http://127.0.0.1:8000/health/ready
```

Start the frontend in API mode in a separate terminal:

```bash
cd frontend
VITE_DATA_MODE=api VITE_API_BASE_URL=/api/v1 API_PROXY_TARGET=http://127.0.0.1:8100 bun run dev --host 127.0.0.1
```

Register a dedicated fictional test account in the UI, open Pricing, choose Starter, and confirm the browser navigates to the official HTTPS Stripe Checkout host. Verify PostgreSQL persistence without exposing secrets:

```bash
docker compose --project-name nexusai-phase3-stripe exec backend python -m alembic current
docker compose --project-name nexusai-phase3-stripe exec postgres psql -U nexusai -d nexusai -c "SELECT id, sku_snapshot, status, payment_status, fulfillment_status FROM orders ORDER BY created_at DESC LIMIT 5;"
docker compose --project-name nexusai-phase3-stripe exec postgres psql -U nexusai -d nexusai -c "SELECT balance FROM wallets w JOIN users u ON u.id=w.user_id WHERE u.email='dedicated-sandbox@example.test';"
```

Use only an official Stripe Sandbox test card, such as `4242 4242 4242 4242`, any future expiry, and a valid CVC. Never use real card details. After returning, refresh the order status and verify `payment_status=paid` only after Stripe confirms it while `fulfillment_status=pending` and the wallet balance is unchanged. Test cancel, browser refresh, repeat the same `Idempotency-Key`, and use a new key for a legitimate separate purchase.

## Sandbox replacement

When the temporary Sandbox expires, create a new private Sandbox key, verify the new account identity, run the catalogue dry-run/apply/verify procedure, and keep old account-scoped mappings for history. Do not copy old Customer, Product, Price, or Session IDs into the replacement account.
