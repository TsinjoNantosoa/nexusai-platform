from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

import pytest
from app.core.errors import ApiProblem
from app.db.models import Product, User, Wallet, WalletEntry
from app.db.seed import seed_products
from app.db.session import build_session_factory
from app.wallet.service import apply_movement, refund_movement
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_database")]


def csrf_headers(client: TestClient) -> dict[str, str]:
    response = client.get("/api/v1/auth/csrf")
    assert response.status_code == 200
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def register(client: TestClient, email: str = "user@example.test") -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        headers=csrf_headers(client),
        json={
            "email": email,
            "password": "fictional-password-123",
            "age_confirmed": True,
            "terms_accepted": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_health_and_products_are_available(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").status_code == 200
    products = client.get("/api/v1/billing/products")
    assert products.status_code == 200
    assert {(item["sku"], item["priceCents"], item["gems"]) for item in products.json()} == {
        ("free", 0, 20),
        ("starter", 299, 100),
        ("plus", 999, 500),
        ("premium", 1999, 1500),
    }


def test_product_seed_is_idempotent(db_engine: Engine) -> None:
    seed_products()
    seed_products()
    factory = build_session_factory(db_engine)
    with factory() as session:
        assert len(session.execute(select(Product)).all()) == 4


def test_registration_grants_exactly_one_welcome_bonus(client: TestClient) -> None:
    user = register(client)
    assert user["admin"] is False
    assert client.get("/api/v1/users/me").json()["email"] == "user@example.test"
    assert client.get("/api/v1/wallet").json() == {"balance": 20, "inReview": False}
    entries = client.get("/api/v1/wallet/transactions").json()
    assert len(entries) == 1
    assert entries[0]["type"] == "welcome"
    duplicate = client.post(
        "/api/v1/auth/register",
        headers=csrf_headers(client),
        json={
            "email": "user@example.test",
            "password": "fictional-password-123",
            "age_confirmed": True,
            "terms_accepted": True,
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "email_already_registered"


def test_invalid_credentials_and_csrf_are_rejected(client: TestClient) -> None:
    register(client)
    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    invalid = client.post(
        "/api/v1/auth/login",
        headers=csrf_headers(client),
        json={"email": "user@example.test", "password": "wrong-password"},
    )
    assert invalid.status_code == 401
    assert invalid.json()["code"] == "invalid_credentials"
    missing_csrf = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.test", "password": "fictional-password-123"},
    )
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["code"] == "csrf_invalid"


def test_logout_revokes_session_and_accounts_are_isolated(client: TestClient) -> None:
    register(client, "first@example.test")
    assert client.get("/api/v1/wallet").status_code == 200
    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    assert client.get("/api/v1/wallet").status_code == 401
    register(client, "second@example.test")
    assert client.get("/api/v1/users/me").json()["email"] == "second@example.test"
    assert client.get("/api/v1/wallet").json()["balance"] == 20


def test_public_clients_cannot_credit_wallets(client: TestClient) -> None:
    register(client)
    response = client.post(
        "/api/v1/wallet/credit",
        headers=csrf_headers(client),
        json={"amount": 100, "reference": "public-credit"},
    )
    assert response.status_code == 404


def test_regular_users_cannot_access_admin_routes(client: TestClient) -> None:
    register(client)
    response = client.get("/api/v1/admin/reports")
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_wallet_operations_are_idempotent_and_refunds_are_bounded(db_engine: Engine) -> None:
    factory = build_session_factory(db_engine)
    with factory.begin() as session:
        user = User(
            email="wallet@example.test",
            password_hash="not-used-in-service-test",
            role="user",
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
                metadata_json={},
            )
        )
        user_id = user.id
    with factory() as session:
        first = apply_movement(session, user_id, -2, "message", "message:1")
        second = apply_movement(session, user_id, -2, "message", "message:1")
        assert first.id == second.id
    with factory() as session:
        refund = refund_movement(session, user_id, "message:1", 2, "refund:1")
        assert refund.amount == 2
        with pytest.raises(ApiProblem) as error:
            refund_movement(session, user_id, "message:1", 1, "refund:2")
        assert error.value.code == "refund_exceeds_debit"
    with factory() as session:
        wallet = session.execute(select(Wallet).where(Wallet.user_id == user_id)).scalar_one()
        assert wallet.balance == 20


def test_concurrent_debits_never_make_balance_negative(db_engine: Engine) -> None:
    factory = build_session_factory(db_engine)
    with factory.begin() as session:
        user = User(
            email="concurrency@example.test",
            password_hash="not-used-in-service-test",
            role="user",
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
                metadata_json={},
            )
        )
        user_id: UUID = user.id

    def spend(index: int) -> str:
        try:
            with factory() as session:
                apply_movement(session, user_id, -15, "message", f"concurrent:{index}")
            return "ok"
        except ApiProblem as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(spend, range(2)))
    assert sorted(outcomes) == ["insufficient_balance", "ok"]
    with factory() as session:
        wallet = session.execute(select(Wallet).where(Wallet.user_id == user_id)).scalar_one()
        assert wallet.balance == 5


def test_concurrent_duplicate_operations_create_one_entry(db_engine: Engine) -> None:
    factory = build_session_factory(db_engine)
    with factory.begin() as session:
        user = User(
            email="duplicate@example.test",
            password_hash="not-used-in-service-test",
            role="user",
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
                metadata_json={},
            )
        )
        user_id: UUID = user.id

    def spend(_: int) -> str:
        with factory() as session:
            apply_movement(session, user_id, -2, "message", "duplicate-operation")
        return "ok"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(spend, range(2))) == ["ok", "ok"]
    with factory() as session:
        entries = list(
            session.execute(
                select(WalletEntry).where(WalletEntry.reference == "duplicate-operation")
            ).scalars()
        )
        wallet = session.execute(select(Wallet).where(Wallet.user_id == user_id)).scalar_one()
        assert len(entries) == 1
        assert wallet.balance == 18
