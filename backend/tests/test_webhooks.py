from __future__ import annotations

import hashlib
import hmac
import json
import time
from uuid import UUID, uuid4

import pytest
from app.billing.fulfillment import WebhookProcessor
from app.billing.webhooks import enqueue_event
from app.core.config import Settings
from app.db.models import Order, Product, User, Wallet, WalletEntry, WebhookEvent
from app.db.session import build_session_factory
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine

WEBHOOK_SECRET = "whsec_test_phase_3_3"
ACCOUNT_ID = "acct_test_nexusai"
SESSION_ID = "cs_test_webhook"
PRICE_ID = "price_test_starter"
PAYMENT_INTENT_ID = "pi_test_webhook"


class FulfillmentGateway:
    session = {
        "id": SESSION_ID,
        "object": "checkout.session",
        "status": "complete",
        "payment_status": "paid",
        "livemode": False,
        "mode": "payment",
        "client_reference_id": "",
        "metadata": {},
        "customer": "cus_test_webhook",
        "amount_total": 299,
        "currency": "eur",
        "payment_intent": PAYMENT_INTENT_ID,
        "url": None,
    }
    payment_intent = {
        "id": PAYMENT_INTENT_ID,
        "object": "payment_intent",
        "livemode": False,
        "status": "succeeded",
        "amount": 299,
        "amount_received": 299,
        "currency": "eur",
        "customer": "cus_test_webhook",
    }

    def retrieve_checkout_session(self, _session_id: str):
        return dict(self.session)

    def list_checkout_session_line_items(self, _session_id: str):
        return iter(
            [
                {
                    "id": "li_test_webhook",
                    "object": "item",
                    "price": {"id": PRICE_ID},
                    "quantity": 1,
                }
            ]
        )

    def retrieve_price(self, _price_id: str):
        return {
            "id": PRICE_ID,
            "object": "price",
            "product": "prod_test_starter",
            "unit_amount": 299,
            "currency": "eur",
            "type": "one_time",
            "recurring": None,
            "livemode": False,
        }

    def retrieve_payment_intent(self, _payment_intent_id: str):
        return dict(self.payment_intent)


def payload(
    event_id: str,
    event_type: str,
    *,
    live: bool = False,
    account: str = ACCOUNT_ID,
) -> bytes:
    return json.dumps(
        {
            "id": event_id,
            "object": "event",
            "type": event_type,
            "livemode": live,
            "account": account,
            "data": {"object": {"id": SESSION_ID, "object": "checkout.session"}},
        },
        separators=(",", ":"),
    ).encode()


def signature(body: bytes, timestamp: int | None = None) -> str:
    timestamp = timestamp or int(time.time())
    digest = hmac.new(
        WEBHOOK_SECRET.encode(), f"{timestamp}.".encode() + body, hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={digest}"


def webhook_settings(test_database_url: str, *, max_body_bytes: int = 512 * 1024) -> Settings:
    return Settings(
        database_url=test_database_url,
        stripe_enabled=True,
        stripe_secret_key="rkcs_test_placeholder",
        stripe_webhook_secret=WEBHOOK_SECRET,
        stripe_account_id=ACCOUNT_ID,
        stripe_webhook_max_body_bytes=max_body_bytes,
    )


def create_paid_order(db_engine: Engine) -> UUID:
    factory = build_session_factory(db_engine)
    with factory.begin() as session:
        user = User(
            email=f"webhook-{uuid4()}@example.test",
            password_hash="not-used",
            age_confirmed=True,
            terms_accepted=True,
        )
        session.add(user)
        session.flush()
        wallet = Wallet(user_id=user.id, balance=20)
        session.add(wallet)
        session.flush()
        session.add(
            WalletEntry(
                wallet_id=wallet.id,
                amount=20,
                entry_type="welcome",
                reference=f"welcome:{user.id}",
                metadata_json={"reason": "registration_bonus"},
            )
        )
        product = session.execute(select(Product).where(Product.sku == "starter")).scalar_one()
        order = Order(
            user_id=user.id,
            product_id=product.id,
            sku_snapshot="starter",
            name_snapshot="Starter",
            price_cents=299,
            currency="EUR",
            gems=100,
            stripe_account_id=ACCOUNT_ID,
            stripe_product_id="prod_test_starter",
            stripe_price_id=PRICE_ID,
            stripe_customer_id="cus_test_webhook",
            checkout_session_id=SESSION_ID,
            idempotency_key=f"webhook-order-{uuid4()}",
            request_fingerprint="f" * 64,
            checkout_status="created",
        )
        session.add(order)
        session.flush()
        FulfillmentGateway.session["client_reference_id"] = str(order.id)
        FulfillmentGateway.session["metadata"] = {"nexusai_order_id": str(order.id)}
        return order.id


def test_webhook_accepts_valid_signature_without_csrf_and_is_idempotent(
    test_database_url: str, clean_database, db_engine: Engine
) -> None:
    settings = webhook_settings(test_database_url)
    body = payload("evt_valid_webhook", "checkout.session.completed")
    with TestClient(create_app(settings)) as client:
        first = client.post(
            "/api/v1/billing/webhooks/stripe",
            content=body,
            headers={"Stripe-Signature": signature(body)},
        )
        duplicate = client.post(
            "/api/v1/billing/webhooks/stripe",
            content=body,
            headers={"Stripe-Signature": signature(body)},
        )
    assert first.status_code == 200
    assert first.json()["duplicate"] is False
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    with db_engine.connect() as connection:
        assert connection.execute(select(WebhookEvent)).fetchall().__len__() == 1


@pytest.mark.parametrize("headers", [{}, {"Stripe-Signature": "t=1,v1=bad"}])
def test_webhook_rejects_missing_or_invalid_signature(
    test_database_url: str, clean_database, headers: dict[str, str]
) -> None:
    body = payload("evt_invalid_signature", "checkout.session.completed")
    with TestClient(create_app(webhook_settings(test_database_url))) as client:
        response = client.post("/api/v1/billing/webhooks/stripe", content=body, headers=headers)
    assert response.status_code == 400
    assert response.json()["code"] in {"stripe_signature_missing", "stripe_signature_invalid"}


def test_webhook_rejects_expired_and_live_events(test_database_url: str, clean_database) -> None:
    body = payload("evt_expired_signature", "checkout.session.completed")
    live_body = payload("evt_live", "checkout.session.completed", live=True)
    with TestClient(create_app(webhook_settings(test_database_url))) as client:
        expired = client.post(
            "/api/v1/billing/webhooks/stripe",
            content=body,
            headers={"Stripe-Signature": signature(body, int(time.time()) - 1000)},
        )
        live = client.post(
            "/api/v1/billing/webhooks/stripe",
            content=live_body,
            headers={"Stripe-Signature": signature(live_body)},
        )
    assert expired.status_code == 400
    assert live.status_code == 400
    assert live.json()["code"] == "stripe_event_invalid"


def test_webhook_rejects_malformed_account_and_oversized_payload(
    test_database_url: str, clean_database
) -> None:
    with TestClient(create_app(webhook_settings(test_database_url))) as client:
        body = payload("evt_wrong_account", "checkout.session.completed", account="acct_other")
        wrong_account = client.post(
            "/api/v1/billing/webhooks/stripe",
            content=body,
            headers={"Stripe-Signature": signature(body)},
        )
        malformed_body = b"{}"
        malformed = client.post(
            "/api/v1/billing/webhooks/stripe",
            content=malformed_body,
            headers={"Stripe-Signature": signature(malformed_body)},
        )
    with TestClient(create_app(webhook_settings(test_database_url, max_body_bytes=32))) as client:
        oversized = client.post(
            "/api/v1/billing/webhooks/stripe",
            content=b"x" * 33,
            headers={"Stripe-Signature": signature(b"x" * 33)},
        )
    assert wrong_account.status_code == 400
    assert wrong_account.json()["code"] == "stripe_account_mismatch"
    assert malformed.status_code == 400
    assert malformed.json()["code"] == "stripe_event_invalid"
    assert oversized.status_code == 413


def test_paid_event_fulfills_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: str,
    clean_database,
    db_engine: Engine,
) -> None:
    order_id = create_paid_order(db_engine)
    settings = webhook_settings(test_database_url)
    gateway = FulfillmentGateway()
    monkeypatch.setattr("app.billing.fulfillment.StripeClient", lambda _settings: gateway)
    factory = build_session_factory(db_engine)
    with factory() as session:
        first_body = payload("evt_paid_one", "checkout.session.completed")
        second_body = payload("evt_paid_two", "checkout.session.async_payment_succeeded")
        first, _ = enqueue_event(session, settings, first_body, signature(first_body))
        second, _ = enqueue_event(session, settings, second_body, signature(second_body))
        processor = WebhookProcessor(session, settings)
        assert processor.process_one(_claim(processor, first.id)) == "completed"
        assert processor.process_one(_claim(processor, second.id)) == "completed"
    with factory() as session:
        order = session.get(Order, order_id)
        wallet = session.execute(select(Wallet).where(Wallet.user_id == order.user_id)).scalar_one()
        entries = list(
            session.execute(select(WalletEntry).where(WalletEntry.wallet_id == wallet.id)).scalars()
        )
        assert order.fulfillment_status == "fulfilled"
        assert wallet.balance == 120
        assert len([entry for entry in entries if entry.entry_type == "purchase"]) == 1


def _claim(processor: WebhookProcessor, event_id: UUID) -> UUID:
    claimed = processor.claim_next()
    assert claimed == event_id
    return claimed


def test_unpaid_event_does_not_credit_wallet(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: str,
    clean_database,
    db_engine: Engine,
) -> None:
    order_id = create_paid_order(db_engine)
    FulfillmentGateway.session["payment_status"] = "unpaid"
    settings = webhook_settings(test_database_url)
    monkeypatch.setattr(
        "app.billing.fulfillment.StripeClient", lambda _settings: FulfillmentGateway()
    )
    factory = build_session_factory(db_engine)
    with factory() as session:
        body = payload("evt_expired_order", "checkout.session.expired")
        event, _ = enqueue_event(session, settings, body, signature(body))
        processor = WebhookProcessor(session, settings)
        assert processor.process_one(_claim(processor, event.id)) == "completed"
    with factory() as session:
        order = session.get(Order, order_id)
        wallet = session.execute(select(Wallet).where(Wallet.user_id == order.user_id)).scalar_one()
        assert order.status == "expired"
        assert order.fulfillment_status == "pending"
        assert wallet.balance == 20
