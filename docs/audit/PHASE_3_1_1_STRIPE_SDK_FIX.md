# Phase 3.1.1 Stripe SDK compatibility fix

## Confirmed root cause

The owner’s read-only Sandbox diagnostic showed that Stripe SDK 17.1.0 returned a `StripeResponse` from `raw_request("get", "/v1/account")`. `StripeResponse` is not a `Mapping` and does not expose the account ID directly. The SDK’s validated path is to call `client.deserialize(response, api_mode="V1")`, then convert the resulting `Account` resource with `to_dict()`.

The previous automated tests missed this defect because their gateway returned ordinary dictionaries. They did not exercise the SDK’s raw response or `StripeObject` runtime types.

## Correction

`app.billing.stripe_client` now provides one normalization boundary for account, product, and price responses. It:

- deserializes raw `StripeResponse` objects with the pinned SDK and explicit `V1` mode;
- recursively converts `StripeObject`, nested metadata, recurring data, mappings, and paginated resources to plain dictionaries;
- preserves IDs and field values without fabricating an absent `livemode` field;
- rejects missing IDs, unsupported object types, malformed responses, and deserialization failures with sanitized error codes;
- keeps pagination, stable idempotency keys, explicit API version, timeout, and retry settings unchanged.

The catalogue layer remains responsible for account ID validation, explicit `livemode=true` rejection, amounts, currencies, recurrence, metadata, uniqueness, and account-scoped mappings. Dictionary-based gateways remain supported for controlled tests.

## Regression evidence

The regression suite constructs real `stripe.StripeResponse`, `Account`, `Product`, and `Price` objects locally with `stripe==17.1.0`; it never calls the Stripe API. Coverage includes the original raw account failure, account deserialization, missing/invalid IDs, absent and explicit live mode, nested metadata/recurrence, pagination, SDK-object reuse, malformed responses, sanitized errors, live products/prices, and dictionary gateways.

The pre-fix behavior was reproduced by passing a raw `StripeResponse` to account validation and observing the same missing/invalid identity failure. The corrected account path now returns the normalized account ID.

Validation results:

- `backend/.venv/Scripts/ruff.exe check app migrations tests` — PASS.
- `backend/.venv/Scripts/pytest.exe tests/test_stripe_catalogue.py -q` — PASS, 21 tests.
- `backend/.venv/Scripts/pytest.exe tests -q` — PASS, 63 tests, one existing Starlette/httpx deprecation warning.
- `backend/.venv/Scripts/python.exe -m pip_audit --local` — PASS, no known vulnerabilities; the local package was skipped because it is not published on PyPI.
- Frontend `bun install --frozen-lockfile`, lint, typecheck, Vitest, and build — PASS; 37 tests, 10 existing lint warnings, 48 PWA precache entries.
- `bun audit` — exit 1 with the two previously documented moderate `glob` and `minimatch` advisories.
- Compose configuration and tracked-file secret scan — PASS; no exposed live/private key or webhook-secret patterns detected.

## Limitations

No owner credentials were read, no `--apply` command was executed, and no Stripe resource was created. The owner must rerun the real Sandbox `--dry-run` after rebuilding the backend. Checkout, webhooks, subscriptions, refunds, and Phase 3.2 remain out of scope.
