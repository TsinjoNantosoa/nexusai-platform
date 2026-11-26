from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from types import SimpleNamespace
from typing import Any

import pytest
import stripe
from app.billing.catalogue import (
    CatalogueBootstrapError,
    _account_identity,
    _assert_sandbox_resource,
    run_catalogue_bootstrap,
)
from app.billing.stripe_client import (
    StripeClient,
    StripeClientError,
    normalize_stripe_resource,
)
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


def sdk_resource(payload: dict[str, Any]) -> Any:
    sdk = stripe.StripeClient("rkcs_test_placeholder")
    response = stripe.StripeResponse(json.dumps(payload), 200, {})
    return sdk.deserialize(response, api_mode="V1")


class SdkObjectGateway(FakeStripeGateway):
    def account(self):
        return sdk_resource({"id": self.account_id, "object": "account"})

    def list_products(self):
        return iter([sdk_resource(product) for product in self.products])

    def create_product(self, params, idempotency_key: str):
        super().create_product(params, idempotency_key)
        return sdk_resource(self.products[-1])

    def list_prices(self):
        return iter([sdk_resource(price) for price in self.prices])

    def create_price(self, params, idempotency_key: str):
        super().create_price(params, idempotency_key)
        return sdk_resource(self.prices[-1])


def test_real_stripe_response_account_is_deserialized_and_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = StripeClient(
        Settings(
            stripe_enabled=True,
            stripe_secret_key="rkcs_test_placeholder",
            stripe_webhook_secret="whsec_placeholder",
        )
    )
    response = stripe.StripeResponse(
        json.dumps({"id": "acct_test_real_response", "object": "account"}), 200, {}
    )
    monkeypatch.setattr(client._client, "raw_request", lambda *_args: response)

    account = client.account()

    assert account == {"id": "acct_test_real_response", "object": "account"}
    assert _account_identity(account) == "acct_test_real_response"


@pytest.mark.parametrize(
    "payload, expected_code",
    [
        ({"object": "account"}, "response_invalid"),
        ({"id": "not-an-account", "object": "account"}, "invalid"),
    ],
)
def test_account_identifier_validation_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, Any],
    expected_code: str,
) -> None:
    if expected_code == "response_invalid":
        client = StripeClient(
            Settings(
                stripe_enabled=True,
                stripe_secret_key="rkcs_test_placeholder",
                stripe_webhook_secret="whsec_placeholder",
            )
        )
        response = stripe.StripeResponse(json.dumps(payload), 200, {})
        monkeypatch.setattr(client._client, "raw_request", lambda *_args: response)
        with pytest.raises(StripeClientError, match="response_invalid"):
            client.account()
    else:
        with pytest.raises(CatalogueBootstrapError, match="missing or invalid"):
            _account_identity(payload)


def test_account_without_livemode_is_not_fabricated_or_rejected() -> None:
    account = normalize_stripe_resource(
        sdk_resource({"id": "acct_test_without_livemode", "object": "account"}),
        operation="account",
        expected_object="account",
    )

    assert "livemode" not in account
    assert _account_identity(account) == "acct_test_without_livemode"


def test_explicit_live_account_is_rejected() -> None:
    account = normalize_stripe_resource(
        sdk_resource({"id": "acct_live", "object": "account", "livemode": True}),
        operation="account",
        expected_object="account",
    )

    with pytest.raises(CatalogueBootstrapError, match="Live Stripe accounts"):
        _account_identity(account)


@pytest.mark.parametrize(
    "resource, kind",
    [
        ({"id": "prod_live", "livemode": True}, "product"),
        ({"id": "price_live", "livemode": True}, "price"),
    ],
)
def test_explicit_live_product_and_price_resources_are_rejected(
    resource: dict[str, Any], kind: str
) -> None:
    with pytest.raises(CatalogueBootstrapError, match="Live Stripe"):
        _assert_sandbox_resource(resource, kind, "starter")


def test_product_and_price_sdk_objects_are_normalized_with_nested_values() -> None:
    product = sdk_resource(
        {
            "id": "prod_test_sdk",
            "object": "product",
            "name": "NexusAI Starter",
            "active": True,
            "livemode": False,
            "metadata": {"nexusai_sku": "starter"},
        }
    )
    price = sdk_resource(
        {
            "id": "price_test_sdk",
            "object": "price",
            "product": "prod_test_sdk",
            "active": True,
            "livemode": False,
            "unit_amount": 1999,
            "currency": "eur",
            "lookup_key": "nexusai_premium",
            "recurring": {"interval": "month", "interval_count": 1},
            "metadata": {"nexusai_sku": "premium"},
        }
    )

    normalized_product = normalize_stripe_resource(
        product, operation="product", expected_object="product"
    )
    normalized_price = normalize_stripe_resource(price, operation="price", expected_object="price")

    assert normalized_product["metadata"] == {"nexusai_sku": "starter"}
    assert normalized_price["metadata"] == {"nexusai_sku": "premium"}
    assert normalized_price["recurring"] == {"interval": "month", "interval_count": 1}


def test_client_normalizes_paginated_and_created_sdk_resources() -> None:
    product = sdk_resource(
        {
            "id": "prod_test_page",
            "object": "product",
            "name": "NexusAI Starter",
            "active": True,
            "livemode": False,
            "metadata": {"nexusai_sku": "starter"},
        }
    )
    price = sdk_resource(
        {
            "id": "price_test_page",
            "object": "price",
            "product": "prod_test_page",
            "active": True,
            "livemode": False,
            "unit_amount": 299,
            "currency": "eur",
            "lookup_key": "nexusai_starter",
            "recurring": None,
            "metadata": {"nexusai_sku": "starter"},
        }
    )

    class Listing:
        def __init__(self, resources):
            self.resources = resources

        def auto_paging_iter(self):
            return iter(self.resources)

    class ResourceService:
        def __init__(self, resource):
            self.resource = resource
            self.options = None

        def list(self, _params):
            return Listing([self.resource])

        def create(self, _params, options):
            self.options = options
            return self.resource

    sdk = stripe.StripeClient("rkcs_test_placeholder")
    products = ResourceService(product)
    prices = ResourceService(price)
    client = object.__new__(StripeClient)
    client._client = SimpleNamespace(
        deserialize=sdk.deserialize,
        v1=SimpleNamespace(products=products, prices=prices),
    )

    assert list(client.list_products())[0]["id"] == "prod_test_page"
    assert client.create_product({}, "product-key")["metadata"] == {
        "nexusai_sku": "starter"
    }
    assert list(client.list_prices())[0]["id"] == "price_test_page"
    assert client.create_price({}, "price-key")["recurring"] is None
    assert products.options == {"idempotency_key": "product-key"}
    assert prices.options == {"idempotency_key": "price-key"}


def test_client_normalizes_checkout_line_items_with_stripe_item_object() -> None:
    sdk = stripe.StripeClient("rkcs_test_placeholder")
    line_item = sdk_resource(
        {
            "id": "li_test_checkout",
            "object": "item",
            "price": {"id": "price_test_page", "object": "price"},
            "quantity": 1,
        }
    )

    class Listing:
        def auto_paging_iter(self):
            return iter([line_item])

    class LineItemsService:
        def list(self, _session_id, _params):
            return Listing()

    client = object.__new__(StripeClient)
    client._client = SimpleNamespace(
        deserialize=sdk.deserialize,
        v1=SimpleNamespace(
            checkout=SimpleNamespace(
                sessions=SimpleNamespace(line_items=LineItemsService())
            )
        ),
    )

    items = list(client.list_checkout_session_line_items("cs_test_checkout"))

    assert items[0]["id"] == "li_test_checkout"
    assert items[0]["price"]["id"] == "price_test_page"


def test_malformed_sdk_response_and_deserialization_errors_are_sanitized() -> None:
    with pytest.raises(StripeClientError, match="response_invalid") as malformed:
        normalize_stripe_resource(object(), operation="product")
    assert "object at" not in str(malformed.value)

    class BrokenClient:
        def raw_request(self, *_args):
            return stripe.StripeResponse(
                json.dumps({"id": "acct_test", "object": "account"}), 200, {}
            )

        def deserialize(self, *_args, **_kwargs):
            raise ValueError("raw secret response body")

    client = object.__new__(StripeClient)
    client._client = BrokenClient()
    with pytest.raises(StripeClientError, match="response_invalid") as deserialization:
        client.account()
    assert "raw secret response body" not in str(deserialization.value)


def test_catalogue_reuses_actual_sdk_objects_without_duplicates(
    test_database_url: str, db_engine: Engine, clean_database: None
) -> None:
    gateway = SdkObjectGateway()
    factory = build_session_factory(db_engine)

    run_catalogue_bootstrap(settings_for(test_database_url), "apply", factory, gateway)
    repeated = run_catalogue_bootstrap(settings_for(test_database_url), "apply", factory, gateway)

    assert {plan.product_action for plan in repeated.plans} == {"reused"}
    assert {plan.price_action for plan in repeated.plans} == {"reused"}
    assert len(gateway.products) == 3
    assert len(gateway.prices) == 3


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
