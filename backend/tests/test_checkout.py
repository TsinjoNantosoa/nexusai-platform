from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

import pytest
from app.core.config import Settings
from app.db.models import (
    Order,
    Product,
    StripeCatalogueMapping,
    StripeCustomerMapping,
    Wallet,
)
from app.db.session import build_session_factory
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine


class FakeStripeGateway:
    account_id = "acct_test_nexusai"
    customer_id = "cus_test_nexusai"
    product_ids = {"starter": "prod_test_starter", "plus": "prod_test_plus"}
    price_ids = {"starter": "price_test_starter", "plus": "price_test_plus"}
    sessions: dict[str, dict[str, object]] = {}
    calls: list[tuple[str, object]] = []

    def account(self):
        return {"id": self.account_id, "object": "account", "livemode": False}

    def retrieve_product(self, product_id: str):
        self.calls.append(("retrieve_product", product_id))
        return {"id": product_id, "object": "product", "active": True, "livemode": False}

    def retrieve_price(self, price_id: str):
        self.calls.append(("retrieve_price", price_id))
        sku = next(sku for sku, value in self.price_ids.items() if value == price_id)
        amount = {"starter": 299, "plus": 999}[sku]
        return {
            "id": price_id,
            "object": "price",
            "active": True,
            "currency": "eur",
            "livemode": False,
            "product": self.product_ids[sku],
            "type": "one_time",
            "unit_amount": amount,
            "recurring": None,
        }

    def create_customer(self, params, idempotency_key: str):
        self.calls.append(("create_customer", idempotency_key))
        return {"id": self.customer_id, "object": "customer", "livemode": False}

    def retrieve_customer(self, customer_id: str):
        return {"id": customer_id, "object": "customer", "livemode": False}

    def create_checkout_session(self, params, idempotency_key: str):
        self.calls.append(("create_session", params))
        session_id = f"cs_test_{len(self.sessions) + 1}"
        session = {
            "id": session_id,
            "object": "checkout.session",
            "amount_total": {"price_test_starter": 299, "price_test_plus": 999}[
                params["line_items"][0]["price"]
            ],
            "client_reference_id": params["client_reference_id"],
            "currency": "eur",
            "customer": params["customer"],
            "expires_at": params["expires_at"],
            "livemode": False,
            "metadata": params["metadata"],
            "mode": "payment",
            "payment_intent": None,
            "payment_status": "unpaid",
            "status": "open",
            "url": f"https://checkout.stripe.com/c/pay/{session_id}",
        }
        self.sessions[session_id] = {
            "session": session,
            "items": [{"price": {"id": params["line_items"][0]["price"]}, "quantity": 1}],
        }
        return session

    def retrieve_checkout_session(self, session_id: str):
        return self.sessions[session_id]["session"]

    def list_checkout_session_line_items(self, session_id: str) -> Iterator[dict[str, object]]:
        yield from self.sessions[session_id]["items"]


class FakeStripeClient:
    gateway = FakeStripeGateway()

    def __new__(cls, settings: Settings):
        return cls.gateway


def csrf_headers(client: TestClient) -> dict[str, str]:
    response = client.get("/api/v1/auth/csrf")
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def register(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/v1/auth/register",
        headers=csrf_headers(client),
        json={
            "email": email,
            "password": "CorrectHorseBatteryStaple!123",
            "age_confirmed": True,
            "terms_accepted": True,
        },
    )
    assert response.status_code == 201


@pytest.fixture
def mapped_catalogue(clean_database, db_engine: Engine) -> None:
    factory = build_session_factory(db_engine)
    with factory.begin() as session:
        for product in session.execute(
            select(Product).where(Product.sku.in_(["starter", "plus"]))
        ).scalars():
            session.add(
                StripeCatalogueMapping(
                    product_id=product.id,
                    stripe_account_id=FakeStripeGateway.account_id,
                    stripe_product_id=FakeStripeGateway.product_ids[product.sku],
                    stripe_price_id=FakeStripeGateway.price_ids[product.sku],
                    catalogue_version="nexusai-2026-11-18-v1",
                )
            )


@pytest.fixture(autouse=True)
def reset_fake_gateway() -> None:
    FakeStripeGateway.sessions.clear()
    FakeStripeGateway.calls.clear()


def test_checkout_uses_server_catalogue_and_preserves_wallet(
    client: TestClient,
    mapped_catalogue: None,
    db_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.billing.checkout.StripeClient", FakeStripeClient)
    register(client, "checkout-owner@example.test")
    before = client.get("/api/v1/wallet").json()
    response = client.post(
        "/api/v1/billing/checkout",
        headers={**csrf_headers(client), "Idempotency-Key": "checkout-key-starter"},
        json={"sku": "starter", "price_cents": 1, "gems": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["checkout_url"].startswith("https://checkout.stripe.com/")
    session_params = next(
        value for name, value in FakeStripeGateway.calls if name == "create_session"
    )
    assert session_params["line_items"] == [{"price": "price_test_starter", "quantity": 1}]
    assert client.get("/api/v1/wallet").json() == before

    factory = build_session_factory(db_engine)
    with factory() as session:
        order = session.get(Order, UUID(body["order_id"]))
        assert order is not None
        assert order.price_cents == 299
        assert order.gems == 100
        assert order.fulfillment_status == "pending"
        assert (
            session.execute(select(StripeCustomerMapping)).scalar_one().stripe_customer_id
            == "cus_test_nexusai"
        )
        assert session.execute(select(Wallet)).scalar_one().balance == 20


def test_duplicate_checkout_reuses_session_and_conflicts_are_rejected(
    client: TestClient,
    mapped_catalogue: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.billing.checkout.StripeClient", FakeStripeClient)
    register(client, "idempotency-owner@example.test")
    headers = {**csrf_headers(client), "Idempotency-Key": "same-checkout-key"}
    first = client.post("/api/v1/billing/checkout", headers=headers, json={"sku": "plus"})
    duplicate = client.post("/api/v1/billing/checkout", headers=headers, json={"sku": "plus"})
    conflict = client.post("/api/v1/billing/checkout", headers=headers, json={"sku": "starter"})
    assert first.status_code == duplicate.status_code == 200
    assert first.json()["order_id"] == duplicate.json()["order_id"]
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "idempotency_conflict"
    assert len([name for name, _ in FakeStripeGateway.calls if name == "create_session"]) == 1


def test_duplicate_checkout_rejects_a_session_for_another_customer(
    client: TestClient,
    mapped_catalogue: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.billing.checkout.StripeClient", FakeStripeClient)
    register(client, "customer-binding@example.test")
    headers = {**csrf_headers(client), "Idempotency-Key": "customer-binding-key"}
    first = client.post("/api/v1/billing/checkout", headers=headers, json={"sku": "starter"})
    assert first.status_code == 200
    session_id = next(iter(FakeStripeGateway.sessions))
    FakeStripeGateway.sessions[session_id]["session"]["customer"] = "cus_test_other"

    duplicate = client.post("/api/v1/billing/checkout", headers=headers, json={"sku": "starter"})

    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "payment_verification_failed"


def test_order_status_is_owned_and_payment_does_not_fulfill(
    client: TestClient,
    mapped_catalogue: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.billing.checkout.StripeClient", FakeStripeClient)
    register(client, "status-owner@example.test")
    response = client.post(
        "/api/v1/billing/checkout",
        headers={**csrf_headers(client), "Idempotency-Key": "status-key"},
        json={"sku": "starter"},
    )
    order_id = response.json()["order_id"]
    session_id = next(iter(FakeStripeGateway.sessions))
    FakeStripeGateway.sessions[session_id]["session"].update(
        {"status": "complete", "payment_status": "paid", "payment_intent": "pi_test_checkout"}
    )
    status = client.get(f"/api/v1/billing/orders/{order_id}")
    assert status.status_code == 200
    assert status.json()["status"] == "paid"
    assert status.json()["paymentStatus"] == "paid"
    assert status.json()["fulfillmentStatus"] == "pending"


def test_expired_checkout_reconciles_without_checkout_url(
    client: TestClient,
    mapped_catalogue: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.billing.checkout.StripeClient", FakeStripeClient)
    register(client, "expired-checkout@example.test")
    response = client.post(
        "/api/v1/billing/checkout",
        headers={**csrf_headers(client), "Idempotency-Key": "expired-checkout-key"},
        json={"sku": "starter"},
    )
    assert response.status_code == 200
    order_id = response.json()["order_id"]
    session_id = next(iter(FakeStripeGateway.sessions))
    FakeStripeGateway.sessions[session_id]["session"].update(
        {"status": "expired", "payment_status": "unpaid"}
    )
    FakeStripeGateway.sessions[session_id]["session"].pop("url")

    status = client.get(f"/api/v1/billing/orders/{order_id}")

    assert status.status_code == 200
    assert status.json()["status"] == "expired"
    assert status.json()["paymentStatus"] == "unpaid"
    assert status.json()["fulfillmentStatus"] == "pending"
    assert client.get("/api/v1/wallet").json()["balance"] == 20


def test_live_checkout_response_is_rejected(
    client: TestClient,
    mapped_catalogue: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.billing.checkout.StripeClient", FakeStripeClient)
    register(client, "live-response@example.test")
    original = FakeStripeGateway.create_checkout_session

    def live_session(self, params, idempotency_key):
        response = original(self, params, idempotency_key)
        response["livemode"] = True
        return response

    monkeypatch.setattr(FakeStripeGateway, "create_checkout_session", live_session)
    response = client.post(
        "/api/v1/billing/checkout",
        headers={**csrf_headers(client), "Idempotency-Key": "live-key"},
        json={"sku": "starter"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "stripe_resource_invalid"


def test_checkout_requires_authentication_and_valid_csrf(
    client: TestClient,
    mapped_catalogue: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.billing.checkout.StripeClient", FakeStripeClient)
    anonymous = client.post(
        "/api/v1/billing/checkout",
        headers={**csrf_headers(client), "Idempotency-Key": "anonymous-key"},
        json={"sku": "starter"},
    )
    assert anonymous.status_code == 401
    register(client, "csrf-checkout@example.test")
    invalid_csrf = client.post(
        "/api/v1/billing/checkout",
        headers={"X-CSRF-Token": "invalid", "Idempotency-Key": "csrf-key"},
        json={"sku": "starter"},
    )
    assert invalid_csrf.status_code == 403


def test_free_and_premium_checkout_are_rejected(
    client: TestClient,
    mapped_catalogue: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.billing.checkout.StripeClient", FakeStripeClient)
    register(client, "excluded-products@example.test")
    headers = {**csrf_headers(client), "Idempotency-Key": "excluded-key"}
    free = client.post("/api/v1/billing/checkout", headers=headers, json={"sku": "free"})
    premium = client.post(
        "/api/v1/billing/checkout",
        headers={**headers, "Idempotency-Key": "premium-key"},
        json={"sku": "premium"},
    )
    assert free.status_code == 422
    assert free.json()["code"] == "free_checkout_unavailable"
    assert premium.status_code == 409
    assert premium.json()["code"] == "premium_checkout_unavailable"
