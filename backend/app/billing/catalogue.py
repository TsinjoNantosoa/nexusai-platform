from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.db.models import Product, StripeCatalogueMapping

from .stripe_client import StripeClient, StripeGateway, normalize_stripe_value

CATALOGUE_VERSION = "nexusai-2026-11-18-v1"
CATALOGUE_NAMESPACE = "nexusai"
LOCK_KEY = "nexusai:stripe:catalogue:v1"
BootstrapMode = Literal["dry-run", "apply", "verify"]


class CatalogueBootstrapError(RuntimeError):
    pass


@dataclass(frozen=True)
class ApprovedCatalogueItem:
    sku: str
    stripe_name: str
    product_type: str
    price_cents: int
    currency: str
    gems: int
    recurring_interval: str | None = None
    recurring_interval_count: int | None = None


APPROVED_CATALOGUE: dict[str, ApprovedCatalogueItem] = {
    "starter": ApprovedCatalogueItem("starter", "NexusAI Starter", "one_time", 299, "eur", 100),
    "plus": ApprovedCatalogueItem("plus", "NexusAI Plus", "one_time", 999, "eur", 500),
    "premium": ApprovedCatalogueItem(
        "premium", "NexusAI Premium", "recurring", 1999, "eur", 1500, "month", 1
    ),
}


@dataclass(frozen=True)
class CataloguePlan:
    sku: str
    product_action: str
    price_action: str
    stripe_product_id: str | None
    stripe_price_id: str | None


@dataclass(frozen=True)
class CatalogueResult:
    mode: BootstrapMode
    stripe_account_id: str
    plans: tuple[CataloguePlan, ...]


class CatalogueBootstrap:
    def __init__(self, session_factory: sessionmaker[Session], gateway: StripeGateway) -> None:
        self.session_factory = session_factory
        self.gateway = gateway

    def run(self, mode: BootstrapMode) -> CatalogueResult:
        with self.session_factory.begin() as session:
            _acquire_catalogue_lock(session)
            products = _load_and_validate_products(session)
            account = _account_identity(self.gateway.account())
            stripe_products = list(self.gateway.list_products())
            product_resources: dict[str, Mapping[str, Any]] = {}
            plans: list[CataloguePlan] = []

            for sku, specification in APPROVED_CATALOGUE.items():
                product_resource, product_action = self._resolve_product(
                    mode, sku, specification, stripe_products
                )
                if product_resource is not None:
                    product_resources[sku] = product_resource
                plans.append(
                    CataloguePlan(
                        sku,
                        product_action,
                        "pending" if product_resource is None else "pending",
                        _resource_id(product_resource, "product") if product_resource else None,
                        None,
                    )
                )

            stripe_prices = list(self.gateway.list_prices())
            finalized: list[CataloguePlan] = []
            for plan in plans:
                specification = APPROVED_CATALOGUE[plan.sku]
                product_resource = product_resources.get(plan.sku)
                if product_resource is None:
                    finalized.append(
                        CataloguePlan(
                            plan.sku,
                            plan.product_action,
                            "apply-required",
                            None,
                            None,
                        )
                    )
                    continue
                price_resource, price_action = self._resolve_price(
                    mode, specification, product_resource, stripe_prices
                )
                price_id = _resource_id(price_resource, "price") if price_resource else None
                finalized.append(
                    CataloguePlan(
                        plan.sku,
                        plan.product_action,
                        price_action,
                        _resource_id(product_resource, "product"),
                        price_id,
                    )
                )
                if mode == "apply" and price_resource is not None:
                    _persist_mapping(
                        session,
                        products[plan.sku],
                        account,
                        product_resource,
                        price_resource,
                    )

            if mode == "verify":
                _verify_mappings(session, products, account, finalized)
            return CatalogueResult(mode, account, tuple(finalized))

    def _resolve_product(
        self,
        mode: BootstrapMode,
        sku: str,
        specification: ApprovedCatalogueItem,
        resources: Iterable[Mapping[str, Any]],
    ) -> tuple[Mapping[str, Any] | None, str]:
        namespace_resources = [
            resource
            for resource in resources
            if _metadata(resource, "nexusai_catalogue") == CATALOGUE_NAMESPACE
            and _metadata(resource, "nexusai_sku") == sku
        ]
        if any(
            _metadata(resource, "nexusai_catalogue_version") != CATALOGUE_VERSION
            for resource in namespace_resources
        ):
            raise CatalogueBootstrapError(
                f"Stripe product for SKU {sku} belongs to another catalogue version."
            )
        candidates = [
            resource
            for resource in resources
            if _metadata(resource, "nexusai_sku") == sku
            and _metadata(resource, "nexusai_catalogue_version") == CATALOGUE_VERSION
        ]
        if len(candidates) > 1:
            raise CatalogueBootstrapError(f"Ambiguous Stripe product resources for SKU {sku}.")
        if candidates:
            resource = candidates[0]
            _assert_sandbox_resource(resource, "product", sku)
            _validate_product(resource, specification, sku)
            if not _resource_active(resource):
                raise CatalogueBootstrapError(f"Stripe product for SKU {sku} is inactive.")
            return resource, "reused"
        if mode == "verify":
            raise CatalogueBootstrapError(f"Stripe product for SKU {sku} is missing.")
        if mode == "dry-run":
            return None, "create"
        resource = self.gateway.create_product(
            {
                "name": specification.stripe_name,
                "active": True,
                "metadata": _metadata_for(specification),
            },
            _idempotency_key("product", sku),
        )
        _assert_sandbox_resource(resource, "product", sku)
        _validate_product(resource, specification, sku)
        return resource, "created"

    def _resolve_price(
        self,
        mode: BootstrapMode,
        specification: ApprovedCatalogueItem,
        product_resource: Mapping[str, Any],
        resources: Iterable[Mapping[str, Any]],
    ) -> tuple[Mapping[str, Any] | None, str]:
        sku = specification.sku
        lookup_key = _lookup_key(sku)
        product_id = _resource_id(product_resource, "product")
        namespace_resources = [
            resource
            for resource in resources
            if _metadata(resource, "nexusai_catalogue") == CATALOGUE_NAMESPACE
            and _metadata(resource, "nexusai_sku") == sku
        ]
        if any(
            _metadata(resource, "nexusai_catalogue_version") != CATALOGUE_VERSION
            for resource in namespace_resources
        ):
            raise CatalogueBootstrapError(
                f"Stripe price for SKU {sku} belongs to another catalogue version."
            )
        candidates = [
            resource
            for resource in resources
            if (
                _metadata(resource, "nexusai_sku") == sku
                and (
                _metadata(resource, "nexusai_catalogue_version") == CATALOGUE_VERSION
                or _resource_value(resource, "lookup_key") == lookup_key
                )
            )
            or _resource_value(resource, "lookup_key") == lookup_key
        ]
        if len(candidates) > 1:
            raise CatalogueBootstrapError(f"Ambiguous Stripe price resources for SKU {sku}.")
        if candidates:
            resource = candidates[0]
            _assert_sandbox_resource(resource, "price", sku)
            if _resource_value(resource, "product") != product_id:
                raise CatalogueBootstrapError(
                    f"Stripe price for SKU {sku} belongs to another product."
                )
            _validate_price(resource, specification, sku)
            if not _resource_active(resource):
                raise CatalogueBootstrapError(f"Stripe price for SKU {sku} is inactive.")
            return resource, "reused"
        if mode == "verify":
            raise CatalogueBootstrapError(f"Stripe price for SKU {sku} is missing.")
        if mode == "dry-run":
            return None, "create"
        params: dict[str, Any] = {
            "product": product_id,
            "currency": specification.currency,
            "unit_amount": specification.price_cents,
            "lookup_key": lookup_key,
            "metadata": _metadata_for(specification),
        }
        if specification.recurring_interval:
            params["recurring"] = {
                "interval": specification.recurring_interval,
                "interval_count": specification.recurring_interval_count,
            }
        resource = self.gateway.create_price(params, _idempotency_key("price", sku))
        _assert_sandbox_resource(resource, "price", sku)
        if _resource_value(resource, "product") != product_id:
            raise CatalogueBootstrapError(f"Stripe price for SKU {sku} belongs to another product.")
        _validate_price(resource, specification, sku)
        return resource, "created"


def run_catalogue_bootstrap(
    settings: Settings,
    mode: BootstrapMode,
    session_factory: sessionmaker[Session],
    gateway: StripeGateway | None = None,
) -> CatalogueResult:
    resolved_gateway = gateway or StripeClient(settings)
    return CatalogueBootstrap(session_factory, resolved_gateway).run(mode)


def _load_and_validate_products(session: Session) -> dict[str, Product]:
    rows = {
        product.sku: product
        for product in session.execute(select(Product)).scalars()
        if product.sku in {"free", *APPROVED_CATALOGUE}
    }
    expected = {
        "free": ("free", 0, "eur", 20),
        **{
            sku: (item.product_type, item.price_cents, item.currency, item.gems)
            for sku, item in APPROVED_CATALOGUE.items()
        },
    }
    for sku, (product_type, price_cents, currency, gems) in expected.items():
        product = rows.get(sku)
        if product is None:
            raise CatalogueBootstrapError(f"PostgreSQL product SKU {sku} is missing.")
        actual = (product.product_type, product.price_cents, product.currency.lower(), product.gems)
        if actual != (product_type, price_cents, currency, gems) or not product.active:
            raise CatalogueBootstrapError(
                f"PostgreSQL product SKU {sku} conflicts with the approved catalogue."
            )
    return rows


def _persist_mapping(
    session: Session,
    product: Product,
    account_id: str,
    stripe_product: Mapping[str, Any],
    stripe_price: Mapping[str, Any],
) -> None:
    stripe_product_id = _resource_id(stripe_product, "product")
    stripe_price_id = _resource_id(stripe_price, "price")
    mapping = session.execute(
        select(StripeCatalogueMapping).where(
            StripeCatalogueMapping.product_id == product.id,
            StripeCatalogueMapping.stripe_account_id == account_id,
            StripeCatalogueMapping.catalogue_version == CATALOGUE_VERSION,
        )
    ).scalar_one_or_none()
    if mapping is None:
        mapping = StripeCatalogueMapping(
            product_id=product.id,
            stripe_account_id=account_id,
            stripe_product_id=stripe_product_id,
            stripe_price_id=stripe_price_id,
            catalogue_version=CATALOGUE_VERSION,
            synchronized_at=datetime.now(UTC),
        )
        session.add(mapping)
    elif (
        mapping.stripe_product_id != stripe_product_id or mapping.stripe_price_id != stripe_price_id
    ):
        raise CatalogueBootstrapError(
            f"Existing database mapping for SKU {product.sku} conflicts with Stripe resources."
        )
    product.stripe_product_id = stripe_product_id
    product.stripe_price_id = stripe_price_id


def _verify_mappings(
    session: Session,
    products: Mapping[str, Product],
    account_id: str,
    plans: Iterable[CataloguePlan],
) -> None:
    for plan in plans:
        if not plan.stripe_product_id or not plan.stripe_price_id:
            raise CatalogueBootstrapError(
                f"Verification found incomplete mapping for SKU {plan.sku}."
            )
        mapping = session.execute(
            select(StripeCatalogueMapping).where(
                StripeCatalogueMapping.product_id == products[plan.sku].id,
                StripeCatalogueMapping.stripe_account_id == account_id,
                StripeCatalogueMapping.catalogue_version == CATALOGUE_VERSION,
            )
        ).scalar_one_or_none()
        if mapping is None or (
            mapping.stripe_product_id != plan.stripe_product_id
            or mapping.stripe_price_id != plan.stripe_price_id
        ):
            raise CatalogueBootstrapError(
                f"Verification found incomplete mapping for SKU {plan.sku}."
            )


def _acquire_catalogue_lock(session: Session) -> None:
    session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
        {"lock_key": LOCK_KEY},
    )


def _account_identity(account: Mapping[str, Any]) -> str:
    account_id = _resource_value(account, "id")
    if not account_id or not account_id.startswith("acct_"):
        raise CatalogueBootstrapError("Stripe account identity is missing or invalid.")
    if _resource_value(account, "livemode") is True:
        raise CatalogueBootstrapError("Live Stripe accounts are not allowed.")
    return account_id


def _assert_sandbox_resource(resource: Mapping[str, Any], kind: str, sku: str) -> None:
    if _resource_value(resource, "livemode") is True:
        raise CatalogueBootstrapError(f"Live Stripe {kind} resource detected for SKU {sku}.")


def _validate_product(
    resource: Mapping[str, Any], specification: ApprovedCatalogueItem, sku: str
) -> None:
    if _resource_value(resource, "name") != specification.stripe_name:
        raise CatalogueBootstrapError(f"Stripe product for SKU {sku} has a conflicting name.")


def _validate_price(
    resource: Mapping[str, Any], specification: ApprovedCatalogueItem, sku: str
) -> None:
    amount = _resource_value(resource, "unit_amount")
    currency = str(_resource_value(resource, "currency") or "").lower()
    recurring = normalize_stripe_value(_resource_value(resource, "recurring"))
    if amount != specification.price_cents or currency != specification.currency:
        raise CatalogueBootstrapError(
            f"Stripe price for SKU {sku} conflicts with the approved amount or currency."
        )
    if specification.recurring_interval:
        if (
            not isinstance(recurring, Mapping)
            or recurring.get("interval") != specification.recurring_interval
        ):
            raise CatalogueBootstrapError(
                f"Stripe recurring price for SKU {sku} has a conflicting interval."
            )
        if recurring.get("interval_count") != specification.recurring_interval_count:
            raise CatalogueBootstrapError(
                f"Stripe recurring price for SKU {sku} has a conflicting interval count."
            )
    elif recurring is not None:
        raise CatalogueBootstrapError(f"Stripe one-time price for SKU {sku} is recurring.")


def _resource_active(resource: Mapping[str, Any]) -> bool:
    return _resource_value(resource, "active") is not False


def _resource_id(resource: Mapping[str, Any], kind: str) -> str:
    value = _resource_value(resource, "id")
    if not isinstance(value, str) or not value:
        raise CatalogueBootstrapError(f"Stripe {kind} resource has no stable ID.")
    return value


def _resource_value(resource: Mapping[str, Any], key: str) -> Any:
    if isinstance(resource, Mapping):
        return resource.get(key)
    normalized = normalize_stripe_value(resource)
    if isinstance(normalized, Mapping):
        return normalized.get(key)
    return getattr(resource, key, None)


def _metadata(resource: Mapping[str, Any], key: str) -> str | None:
    metadata = normalize_stripe_value(_resource_value(resource, "metadata"))
    if not isinstance(metadata, Mapping):
        return None
    value = metadata.get(key)
    return value if isinstance(value, str) else None


def _metadata_for(specification: ApprovedCatalogueItem) -> dict[str, str]:
    return {
        "nexusai_catalogue": CATALOGUE_NAMESPACE,
        "nexusai_catalogue_version": CATALOGUE_VERSION,
        "nexusai_sku": specification.sku,
        "nexusai_gems": str(specification.gems),
        "nexusai_product_type": specification.product_type,
    }


def _lookup_key(sku: str) -> str:
    return f"nexusai_{sku}_{CATALOGUE_VERSION.replace('-', '_')}"


def _idempotency_key(kind: str, sku: str) -> str:
    return f"{CATALOGUE_NAMESPACE}:catalogue:{CATALOGUE_VERSION}:{kind}:{sku}"
