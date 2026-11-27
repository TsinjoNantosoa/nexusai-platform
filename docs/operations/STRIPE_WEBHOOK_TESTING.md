# Stripe Webhook Testing

Automated tests never access the owner's Sandbox. They use the disposable
PostgreSQL service, fake normalized Stripe SDK responses, and locally generated
signatures.

## Isolated backend tests

From `backend/`, configure the explicit disposable target required by
`AGENTS.md`, keep `NEXUSAI_STRIPE_ENABLED=false`, and run:

```powershell
.\.venv\Scripts\pytest.exe tests/test_webhooks.py -q
.\.venv\Scripts\pytest.exe -q
```

Coverage includes valid, missing, modified, invalid and expired signatures,
live-event rejection, account checks, durable duplicate intake, paid Starter
fulfillment, duplicate event delivery, unpaid/expired no-credit behavior,
PaymentIntent verification and wallet idempotency.

## Local forwarding

The owner may run Stripe CLI in Ubuntu WSL2 only after reviewing the endpoint
and injecting the current listener secret into the backend environment. The
secret must never be copied to the frontend or committed. Use the endpoint
`http://127.0.0.1:8100/api/v1/billing/webhooks/stripe` from Windows; when WSL2
cannot reach that address, use the host-reachable address selected by the owner
and verify the signature secret belongs to that active listener.

Do not run `stripe trigger`, create a Checkout Session, complete a payment, or
fulfill a historical order automatically. An authorized owner demonstration is
the only evidence of real Stripe delivery; automated tests prove isolation and
business invariants only.
