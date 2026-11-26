from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from app.core.config import Settings
from app.core.errors import ApiProblem
from app.db.models import Product, SessionModel, User, Wallet, WalletEntry
from app.db.seed import seed_products
from app.db.session import build_session_factory
from app.main import create_app
from app.wallet.service import apply_movement, create_initial_wallet, refund_movement
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

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


def test_login_rotates_session_and_csrf_tokens(client: TestClient) -> None:
    register(client, "rotation@example.test")
    old_session = client.cookies.get("nexusai_session")
    old_csrf = client.cookies.get("nexusai_csrf")
    login_csrf = csrf_headers(client)["X-CSRF-Token"]
    response = client.post(
        "/api/v1/auth/login",
        headers={"X-CSRF-Token": login_csrf},
        json={"email": "rotation@example.test", "password": "fictional-password-123"},
    )
    assert response.status_code == 200
    assert client.cookies.get("nexusai_session") != old_session
    assert client.cookies.get("nexusai_csrf") != old_csrf

    client.cookies.set("nexusai_session", old_session)
    client.cookies.set("nexusai_csrf", old_csrf)
    assert client.get("/api/v1/users/me").status_code == 401


def test_expired_sessions_cannot_access_protected_resources(
    client: TestClient, db_engine: Engine
) -> None:
    user = register(client, "expired@example.test")
    factory = build_session_factory(db_engine)
    with factory.begin() as session:
        session.query(SessionModel).filter(SessionModel.user_id == UUID(user["id"])).update(
            {SessionModel.expires_at: datetime.now(UTC) - timedelta(minutes=1)}
        )

    assert client.get("/api/v1/users/me").status_code == 401
    assert client.get("/api/v1/wallet").status_code == 401


def test_csrf_rejects_invalid_tokens_without_mutation(
    client: TestClient, test_database_url: str, db_engine: Engine
) -> None:
    register(client, "csrf-a@example.test")
    token_a = csrf_headers(client)["X-CSRF-Token"]
    session_cookie = client.cookies.get("nexusai_session")

    assert client.post("/api/v1/auth/logout").status_code == 403
    assert client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": ""}).status_code == 403
    assert (
        client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": "invalid"}).status_code
        == 403
    )
    forbidden_origin = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": token_a, "Origin": "https://evil.example.test"},
    )
    assert forbidden_origin.status_code == 403
    assert forbidden_origin.json()["code"] == "origin_forbidden"

    with TestClient(create_app(Settings(database_url=test_database_url))) as other_client:
        register(other_client, "csrf-b@example.test")
        token_b = csrf_headers(other_client)["X-CSRF-Token"]
        assert (
            other_client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": token_a}).status_code
            == 403
        )
        assert (
            other_client.post(
                "/api/v1/auth/logout", headers={"X-CSRF-Token": token_b}
            ).status_code
            == 204
        )

    assert client.get("/api/v1/wallet").json()["balance"] == 20
    assert len(client.get("/api/v1/wallet/transactions").json()) == 1
    assert client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": token_a}).status_code == 204

    client.cookies.set("nexusai_session", session_cookie)
    client.cookies.set("nexusai_csrf", token_a)
    assert client.get("/api/v1/users/me").status_code == 401
    assert client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": token_a}).status_code == 401


def test_cross_account_wallet_resources_use_authenticated_ownership(
    client: TestClient, test_database_url: str, db_engine: Engine
) -> None:
    user_a = register(client, "owner-a@example.test")
    with TestClient(create_app(Settings(database_url=test_database_url))) as other_client:
        user_b = register(other_client, "owner-b@example.test")
        factory = build_session_factory(db_engine)
        with factory() as session:
            apply_movement(
                session,
                UUID(user_b["id"]),
                5,
                "internal_credit",
                "cross-account-credit",
            )
            with pytest.raises(ApiProblem) as error:
                apply_movement(
                    session,
                    UUID(user_a["id"]),
                    5,
                    "internal_credit",
                    "cross-account-credit",
                )
            assert error.value.code == "idempotency_conflict"

        assert other_client.get("/api/v1/wallet").json()["balance"] == 25
        assert len(other_client.get("/api/v1/wallet/transactions").json()) == 2
        assert client.get("/api/v1/wallet").json()["balance"] == 20
        assert client.get(f"/api/v1/wallet?user_id={user_b['id']}").json()["balance"] == 20
        assert len(client.get("/api/v1/wallet/transactions").json()) == 1
        assert client.post(
            "/api/v1/wallet/credit",
            headers=csrf_headers(client),
            json={"user_id": user_b["id"], "amount": 5, "reference": "forged"},
        ).status_code == 404


def test_auth_rate_limit_enforces_window_and_ignores_forwarded_header_bypass(
    client: TestClient, test_database_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(
        database_url=test_database_url,
        auth_rate_limit=2,
        auth_rate_window_seconds=10,
    )
    clock = [100.0]
    monkeypatch.setattr("app.core.rate_limit.monotonic", lambda: clock[0])
    with TestClient(create_app(settings)) as limited_client:
        for _ in range(2):
            response = limited_client.post(
                "/api/v1/auth/login",
                headers=csrf_headers(limited_client),
                json={"email": "abuse-a@example.test", "password": "wrong-password"},
            )
            assert response.status_code == 401
        assert (
            limited_client.post(
                "/api/v1/auth/login",
                headers={**csrf_headers(limited_client), "X-Forwarded-For": "203.0.113.9"},
                json={"email": "abuse-a@example.test", "password": "wrong-password"},
            ).status_code
            == 429
        )
        independent = limited_client.post(
            "/api/v1/auth/login",
            headers=csrf_headers(limited_client),
            json={"email": "abuse-b@example.test", "password": "wrong-password"},
        )
        assert independent.status_code == 401
        clock[0] = 111.0
        recovered = limited_client.post(
            "/api/v1/auth/login",
            headers=csrf_headers(limited_client),
            json={"email": "abuse-a@example.test", "password": "wrong-password"},
        )
        assert recovered.status_code == 401


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
        replay = refund_movement(session, user_id, "message:1", 2, "refund:1")
        assert replay.id == refund.id
        with pytest.raises(ApiProblem) as error:
            refund_movement(session, user_id, "message:1", 1, "refund:1")
        assert error.value.code == "idempotency_conflict"
    with factory() as session:
        wallet = session.execute(select(Wallet).where(Wallet.user_id == user_id)).scalar_one()
        entries = list(
            session.execute(select(WalletEntry).where(WalletEntry.wallet_id == wallet.id)).scalars()
        )
        assert wallet.balance == 20
        assert sum(entry.amount for entry in entries) == wallet.balance


def test_welcome_replay_cannot_create_a_second_wallet_or_entry(db_engine: Engine) -> None:
    factory = build_session_factory(db_engine)
    with factory.begin() as session:
        user = User(
            email="welcome-replay@example.test",
            password_hash="not-used-in-service-test",
            role="user",
            age_confirmed=True,
            terms_accepted=True,
        )
        session.add(user)
        session.flush()
        create_initial_wallet(session, user)
        user_id = user.id
    with factory() as session:
        user = session.get(User, user_id)
        assert user is not None
        with pytest.raises(IntegrityError):
            create_initial_wallet(session, user)
        session.rollback()
        assert (
            session.execute(select(Wallet).where(Wallet.user_id == user_id)).scalar_one().balance
            == 20
        )
        assert len(
            session.execute(select(WalletEntry).join(Wallet).where(Wallet.user_id == user_id)).all()
        ) == 1


def test_partial_refunds_remain_bounded_and_conserve_the_ledger(db_engine: Engine) -> None:
    factory = build_session_factory(db_engine)
    with factory.begin() as session:
        user = User(
            email="partial-refund@example.test",
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
        apply_movement(session, user_id, -6, "message", "partial-source")
        refund_movement(session, user_id, "partial-source", 2, "partial-refund-a")
        refund_movement(session, user_id, "partial-source", 4, "partial-refund-b")
    with factory() as session:
        wallet = session.execute(select(Wallet).where(Wallet.user_id == user_id)).scalar_one()
        entries = list(
            session.execute(select(WalletEntry).where(WalletEntry.wallet_id == wallet.id)).scalars()
        )
        assert wallet.balance == 20
        assert sum(entry.amount for entry in entries) == wallet.balance
        assert sum(entry.amount for entry in entries if entry.entry_type == "restitution") == 6


def test_internal_credit_is_atomic_idempotent_and_rejects_conflicts(db_engine: Engine) -> None:
    factory = build_session_factory(db_engine)
    with factory.begin() as session:
        user = User(
            email="internal-credit@example.test",
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
        first = apply_movement(session, user_id, 5, "internal_credit", "credit:1")
        replay = apply_movement(session, user_id, 5, "internal_credit", "credit:1")
        assert first.id == replay.id
        with pytest.raises(ApiProblem) as error:
            apply_movement(session, user_id, 6, "internal_credit", "credit:1")
        assert error.value.code == "idempotency_conflict"
    with factory() as session:
        wallet = session.execute(select(Wallet).where(Wallet.user_id == user_id)).scalar_one()
        entries = list(
            session.execute(select(WalletEntry).where(WalletEntry.wallet_id == wallet.id)).scalars()
        )
        assert wallet.balance == 25
        assert sum(entry.amount for entry in entries) == wallet.balance
        assert len([entry for entry in entries if entry.reference == "credit:1"]) == 1


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
        entries = list(
            session.execute(select(WalletEntry).where(WalletEntry.wallet_id == wallet.id)).scalars()
        )
        assert sum(entry.amount for entry in entries) == wallet.balance


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
        all_entries = list(
            session.execute(select(WalletEntry).where(WalletEntry.wallet_id == wallet.id)).scalars()
        )
        assert sum(entry.amount for entry in all_entries) == wallet.balance


def test_concurrent_refunds_are_bounded_and_idempotent(db_engine: Engine) -> None:
    factory = build_session_factory(db_engine)
    with factory.begin() as session:
        user = User(
            email="refund-concurrency@example.test",
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
        apply_movement(session, user_id, -4, "message", "refund-source")

    def refund(reference: str) -> str:
        try:
            with factory() as session:
                refund_movement(session, user_id, "refund-source", 4, reference)
            return "ok"
        except ApiProblem as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(refund, ["refund-a", "refund-b"]))
    assert sorted(outcomes) == ["ok", "refund_exceeds_debit"]
    with factory() as session:
        wallet = session.execute(select(Wallet).where(Wallet.user_id == user_id)).scalar_one()
        entries = list(
            session.execute(select(WalletEntry).where(WalletEntry.wallet_id == wallet.id)).scalars()
        )
        assert wallet.balance == 20
        assert sum(entry.amount for entry in entries) == wallet.balance
        assert len([entry for entry in entries if entry.entry_type == "restitution"]) == 1
