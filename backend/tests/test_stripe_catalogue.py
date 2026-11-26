from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any

import pytest
from app.billing.catalogue import CatalogueBootstrapError, run_catalogue_bootstrap
from app.billing.stripe_client import StripeClient, StripeClientError
from app.core.config import Settings
from app.db.models import StripeCatalogueMapping, Wallet, WalletEntry
from app.db.session import build_session_factory
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine


class FakeStripeGateway:
    def __init__(self, account_id: str = "acct_test_primary") -> None:
        self.account_id = account_id
        self.products: list[dict[str, Any]] = []
        self.prices: list[dict[str, Any]] = []
        self.created_product_idempotency_keys: list[str] = []
        self.created_price_idempotency_keys: list[str] = []
        self.fail_after_price_sku: str | None = None
        self._lock = Lock()
        self._next_id = 1

    def account(self) -> dict[str, Any]:
        return {"id": self.account_id, "livemode": False}

    def list_products(self):
        with self._lock:
            return iter([dict(product) for product in self.products])

    def create_product(self, params, idempotency_key: str):
        with self._lock:
            self.created_product_idempotency_keys.append(idempotency_key)
            resource = {
                "id": f"prod_{self.account_id}_{self._next_id}",
                "active": True,
                "livemode": False,
                **dict(params),
            }
            self._next_id += 1
            self.products.append(resource)
            return resource

    def list_prices(self):
        with self._lock:
            return iter([dict(price) for price in self.prices])

    def create_price(self, params, idempotency_key: str):
        with self._lock:
            self.created_price_idempotency_keys.append(idempotency_key)
            resource = {
                "id": f"price_{self.account_id}_{self._next_id}",
                "active": True,
                "livemode": False,
                **dict(params),
            }
            self._next_id += 1
            self.prices.append(resource)
            sku = resource["metadata"]["nexusai_sku"]
            if sku == self.fail_after_price_sku:
                self.fail_after_price_sku = None
                raise StripeClientError("price creation", "network_error")
            return resource


def settings_for(test_database_url: str) -> Settings:
    return Settings(database_url=test_database_url)


def test_disabled_stripe_client_never_constructs_a_network_client() -> None:
    with pytest.raises(StripeClientError, match="stripe_disabled"):
        StripeClient(Settings(stripe_enabled=False))


def test_stripe_client_configures_explicit_version_timeout_and_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeHttpClient:
        def __init__(self, **kwargs):
            captured["http"] = kwargs

    class FakeSdkClient:
        def __init__(self, key, **kwargs):
            captured["key"] = key
            captured["sdk"] = kwargs

    monkeypatch.setattr("app.billing.stripe_client.RequestsClient", FakeHttpClient)
    monkeypatch.setattr("app.billing.stripe_client.StripeSdkClient", FakeSdkClient)
    settings = Settings(
        stripe_enabled=True,
        stripe_secret_key="rkcs_test_placeholder",
        stripe_webhook_secret="whsec_placeholder",
        stripe_request_timeout_seconds=17,
        stripe_max_network_retries=1,
    )

    StripeClient(settings)

    assert captured["key"] == "rkcs_test_placeholder"
    assert captured["http"] == {"timeout": 17}
    assert captured["sdk"]["stripe_version"] == "2026-11-18.endive"
    assert captured["sdk"]["max_network_retries"] == 1


def test_live_stripe_account_is_rejected(
    test_database_url: str, db_engine: Engine, clean_database: None
) -> None:
    gateway = FakeStripeGateway()
    gateway.account = lambda: {"id": "acct_live", "livemode": True}

    with pytest.raises(CatalogueBootstrapError, match="Live Stripe accounts"):
        run_catalogue_bootstrap(
            settings_for(test_database_url),
            "dry-run",
            build_session_factory(db_engine),
            gateway,
        )


def test_dry_run_is_read_only_and_excludes_free(
    test_database_url: str, db_engine: Engine, clean_database: None
) -> None:
    gateway = FakeStripeGateway()
    factory = build_session_factory(db_engine)

    result = run_catalogue_bootstrap(settings_for(test_database_url), "dry-run", factory, gateway)

    assert len(result.plans) == 3
    assert {plan.sku for plan in result.plans} == {"starter", "plus", "premium"}
    assert all(plan.product_action == "create" for plan in result.plans)
    assert gateway.products == []
    assert gateway.prices == []
    with factory() as session:
        assert session.execute(select(StripeCatalogueMapping)).all() == []


def test_apply_uses_approved_amounts_recurring_rules_and_persists_mappings(
    test_database_url: str, db_engine: Engine, clean_database: None
) -> None:
    gateway = FakeStripeGateway()
    factory = build_session_factory(db_engine)

    result = run_catalogue_bootstrap(settings_for(test_database_url), "apply", factory, gateway)

    assert len(gateway.products) == 3
    assert len(gateway.prices) == 3
    prices = {price["metadata"]["nexusai_sku"]: price for price in gateway.prices}
    assert (prices["starter"]["unit_amount"], prices["starter"]["currency"]) == (299, "eur")
    assert (prices["plus"]["unit_amount"], prices["plus"]["currency"]) == (999, "eur")
    assert prices["premium"]["unit_amount"] == 1999
    assert prices["premium"]["recurring"] == {"interval": "month", "interval_count": 1}
    assert {plan.price_action for plan in result.plans} == {"created"}
    with factory() as session:
        mappings = list(session.execute(select(StripeCatalogueMapping)).scalars())
        assert len(mappings) == 3
        assert session.execute(select(Wallet)).scalars().all() == []
        assert session.execute(select(WalletEntry)).scalars().all() == []


def test_repeated_apply_reuses_resources_and_verify_is_read_only(
    test_database_url: str, db_engine: Engine, clean_database: None
) -> None:
    gateway = FakeStripeGateway()
    factory = build_session_factory(db_engine)
    run_catalogue_bootstrap(settings_for(test_database_url), "apply", factory, gateway)

    repeated = run_catalogue_bootstrap(settings_for(test_database_url), "apply", factory, gateway)
    verified = run_catalogue_bootstrap(settings_for(test_database_url), "verify", factory, gateway)

    assert len(gateway.products) == 3
    assert len(gateway.prices) == 3
    assert {plan.product_action for plan in repeated.plans} == {"reused"}
    assert {plan.price_action for plan in repeated.plans} == {"reused"}
    assert {plan.price_action for plan in verified.plans} == {"reused"}
    assert len(gateway.created_product_idempotency_keys) == 3
    assert len(gateway.created_price_idempotency_keys) == 3


def test_conflicting_existing_price_is_rejected_without_replacement(
    test_database_url: str, db_engine: Engine, clean_database: None
) -> None:
    gateway = FakeStripeGateway()
    factory = build_session_factory(db_engine)
    run_catalogue_bootstrap(settings_for(test_database_url), "apply", factory, gateway)
    gateway.prices[0]["unit_amount"] = 1
    created_before = len(gateway.prices)

    with pytest.raises(CatalogueBootstrapError, match="conflicts"):
        run_catalogue_bootstrap(settings_for(test_database_url), "apply", factory, gateway)

    assert len(gateway.prices) == created_before


def test_partial_network_failure_recovers_on_repeat(
    test_database_url: str, db_engine: Engine, clean_database: None
) -> None:
    gateway = FakeStripeGateway()
    gateway.fail_after_price_sku = "starter"
    factory = build_session_factory(db_engine)

    with pytest.raises(StripeClientError):
        run_catalogue_bootstrap(settings_for(test_database_url), "apply", factory, gateway)
    assert len(gateway.products) == 3
    assert len(gateway.prices) == 1
    assert gateway.prices[0]["metadata"]["nexusai_sku"] == "starter"

    result = run_catalogue_bootstrap(settings_for(test_database_url), "apply", factory, gateway)

    assert len(gateway.products) == 3
    assert len(gateway.prices) == 3
    assert {plan.price_action for plan in result.plans} == {"reused", "created"}


def test_catalogue_is_account_scoped_when_sandbox_is_replaced(
    test_database_url: str, db_engine: Engine, clean_database: None
) -> None:
    factory = build_session_factory(db_engine)
    first_gateway = FakeStripeGateway("acct_test_expired")
    second_gateway = FakeStripeGateway("acct_test_replacement")

    run_catalogue_bootstrap(settings_for(test_database_url), "apply", factory, first_gateway)
    run_catalogue_bootstrap(settings_for(test_database_url), "apply", factory, second_gateway)

    with factory() as session:
        mappings = list(session.execute(select(StripeCatalogueMapping)).scalars())
        assert {mapping.stripe_account_id for mapping in mappings} == {
            "acct_test_expired",
            "acct_test_replacement",
        }
        assert len(mappings) == 6
        assert {
            mapping.stripe_product_id
            for mapping in mappings
            if mapping.stripe_account_id == "acct_test_expired"
        }.isdisjoint(
            {
                mapping.stripe_product_id
                for mapping in mappings
                if mapping.stripe_account_id == "acct_test_replacement"
            }
        )


def test_concurrent_bootstrap_runs_are_serialized(
    test_database_url: str, db_engine: Engine, clean_database: None
) -> None:
    gateway = FakeStripeGateway()
    second_engine = create_engine(test_database_url, pool_pre_ping=True)
    first_factory = build_session_factory(db_engine)
    second_factory = build_session_factory(second_engine)
    settings = settings_for(test_database_url)

    def run(factory) -> tuple[str, ...]:
        result = run_catalogue_bootstrap(settings, "apply", factory, gateway)
        return tuple(plan.product_action for plan in result.plans)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(run, [first_factory, second_factory]))

    assert set(outcomes) == {
        ("reused", "reused", "reused"),
        ("created", "created", "created"),
    }
    second_engine.dispose()
