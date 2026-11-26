from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApiProblem
from app.db.models import Order, Product, StripeCatalogueMapping, StripeCustomerMapping, User

from .catalogue import (
    APPROVED_CATALOGUE,
    CATALOGUE_VERSION,
    CatalogueBootstrapError,
    _account_identity,
)
from .stripe_client import StripeClient, StripeClientError, StripeGateway

CHECKOUT_EXPIRATION = timedelta(minutes=30)


@dataclass(frozen=True)
class CheckoutResult:
    order: Order
    checkout_url: str


class CheckoutService:
    def __init__(self, db: Session, settings: Settings, user: User) -> None:
        self.db = db
        self.settings = settings
        self.user_id = user.id

    def create(self, sku: str, idempotency_key: str) -> CheckoutResult:
        self._validate_requested_sku(sku)
        fingerprint = _fingerprint(sku)
        self.db.rollback()
        existing = self.db.execute(
            select(Order).where(Order.idempotency_key == idempotency_key)
        ).scalar_one_or_none()
        if existing is not None:
            self._assert_idempotency_compatible(existing, fingerprint)
            if existing.checkout_session_id:
                gateway, account_id = self._gateway_and_account()
                return self._existing_checkout(existing, gateway, account_id)
            if existing.checkout_status in {"creating", "unknown"}:
                raise ApiProblem(
                    "checkout_recovery_required",
                    409,
                    "This checkout attempt requires recovery before another session "
                    "can be created.",
                )
            order = existing
        else:
            gateway, account_id = self._gateway_and_account()
            product, mapping = self._authoritative_product(sku, account_id, gateway)
            order = self._reserve_order(product, mapping, account_id, idempotency_key, fingerprint)
            if order is None:
                existing = self.db.execute(
                    select(Order).where(Order.idempotency_key == idempotency_key)
                ).scalar_one()
                self._assert_idempotency_compatible(existing, fingerprint)
                if existing.checkout_session_id:
                    return self._existing_checkout(existing, gateway, account_id)
                raise ApiProblem(
                    "checkout_in_progress", 409, "The checkout request is already in progress."
                )

        if "gateway" not in locals():
            gateway, account_id = self._gateway_and_account()
            self._assert_order_account(order, account_id)
            self._validate_snapshot(order, gateway)

        customer_id = self._ensure_customer(gateway, account_id)
        self._mark_order_creating(order.id)
        expires_at = datetime.now(UTC) + CHECKOUT_EXPIRATION
        try:
            session = gateway.create_checkout_session(
                self._session_params(order, customer_id, expires_at),
                f"nexusai-checkout-{order.id}",
            )
            checkout_url = _validate_checkout_session(
                session, order, customer_id, require_unpaid=True
            )
        except ApiProblem:
            self._mark_order_unknown(order.id)
            raise
        except StripeClientError:
            self._mark_order_unknown(order.id)
            raise ApiProblem(
                "checkout_recovery_required",
                503,
                "The checkout session could not be confirmed. Retry only after recovery.",
            ) from None
        except Exception:
            self._mark_order_unknown(order.id)
            raise ApiProblem(
                "checkout_recovery_required",
                503,
                "The checkout session could not be confirmed. Retry only after recovery.",
            ) from None

        payment_intent_id = _resource_id(session.get("payment_intent"))
        try:
            self.db.rollback()
            with self.db.begin():
                stored = self.db.execute(
                    select(Order).where(Order.id == order.id).with_for_update()
                ).scalar_one()
                stored.checkout_session_id = session["id"]
                stored.stripe_customer_id = customer_id
                stored.payment_intent_id = payment_intent_id
                stored.checkout_status = "created"
                stored.session_expires_at = (
                    _timestamp_datetime(session.get("expires_at")) or expires_at
                )
        except Exception:
            self._mark_order_unknown(order.id)
            raise ApiProblem(
                "checkout_recovery_required",
                503,
                "The checkout session was created but could not be persisted safely.",
            ) from None
        return CheckoutResult(stored, checkout_url)

    def get(self, order_id: UUID) -> Order:
        self.db.rollback()
        order = self.db.execute(
            select(Order).where(Order.id == order_id, Order.user_id == self.user_id)
        ).scalar_one_or_none()
        if order is None:
            raise ApiProblem("order_not_found", 404, "Order not found.")
        if not order.checkout_session_id:
            return order
        gateway, account_id = self._gateway_and_account()
        self._assert_order_account(order, account_id)
        self._validate_snapshot(order, gateway)
        self._refresh_from_session(order, gateway)
        self.db.refresh(order)
        return order

    def list_orders(self) -> list[Order]:
        self.db.rollback()
        return list(
            self.db.execute(
                select(Order)
                .where(Order.user_id == self.user_id)
                .order_by(Order.created_at.desc(), Order.id.desc())
                .limit(50)
            ).scalars()
        )

    def _gateway_and_account(self) -> tuple[StripeGateway, str]:
        try:
            gateway: StripeGateway = StripeClient(self.settings)
            account = _account_identity(gateway.account())
            return gateway, account
        except (StripeClientError, CatalogueBootstrapError):
            raise ApiProblem(
                "stripe_unavailable",
                503,
                "Stripe Checkout is not available in the configured Sandbox.",
            ) from None

    def _authoritative_product(
        self, sku: str, account_id: str, gateway: StripeGateway
    ) -> tuple[Product, StripeCatalogueMapping]:
        specification = APPROVED_CATALOGUE.get(sku)
        if specification is None:
            if sku == "free":
                raise ApiProblem(
                    "free_checkout_unavailable", 422, "The free offer has no Checkout session."
                )
            if sku == "premium":
                raise ApiProblem(
                    "premium_checkout_unavailable",
                    409,
                    "Premium subscriptions are not available yet.",
                )
            raise ApiProblem("product_unavailable", 422, "The selected product is not available.")
        if specification.product_type != "one_time":
            raise ApiProblem(
                "premium_checkout_unavailable", 409, "Premium subscriptions are not available yet."
            )
        product = self.db.execute(
            select(Product).where(Product.sku == sku, Product.active.is_(True))
        ).scalar_one_or_none()
        if product is None:
            raise ApiProblem("product_unavailable", 409, "The selected product is not available.")
        if (
            product.product_type != "one_time"
            or product.price_cents != specification.price_cents
            or product.currency.lower() != specification.currency
            or product.gems != specification.gems
        ):
            raise ApiProblem(
                "catalogue_conflict", 409, "The selected product catalogue is inconsistent."
            )
        mapping = self.db.execute(
            select(StripeCatalogueMapping).where(
                StripeCatalogueMapping.product_id == product.id,
                StripeCatalogueMapping.stripe_account_id == account_id,
                StripeCatalogueMapping.catalogue_version == CATALOGUE_VERSION,
            )
        ).scalar_one_or_none()
        if mapping is None:
            raise ApiProblem(
                "catalogue_mapping_missing", 503, "The selected product is not ready for Checkout."
            )
        self._validate_mapping_resources(mapping, product, gateway)
        return product, mapping

    @staticmethod
    def _validate_requested_sku(sku: str) -> None:
        if sku == "free":
            raise ApiProblem(
                "free_checkout_unavailable", 422, "The free offer has no Checkout session."
            )
        if sku == "premium":
            raise ApiProblem(
                "premium_checkout_unavailable",
                409,
                "Premium subscriptions are not available yet.",
            )
        if sku not in {"starter", "plus"}:
            raise ApiProblem("product_unavailable", 422, "The selected product is not available.")

    def _validate_mapping_resources(
        self, mapping: StripeCatalogueMapping, product: Product, gateway: StripeGateway
    ) -> None:
        try:
            stripe_product = gateway.retrieve_product(mapping.stripe_product_id)
            stripe_price = gateway.retrieve_price(mapping.stripe_price_id)
        except StripeClientError:
            raise ApiProblem(
                "stripe_unavailable", 503, "The selected product cannot be verified."
            ) from None
        if _is_live(stripe_product) or _is_live(stripe_price):
            raise ApiProblem(
                "stripe_resource_invalid", 409, "The selected Sandbox resources are invalid."
            )
        if (
            stripe_product.get("id") != mapping.stripe_product_id
            or stripe_product.get("active") is not True
        ):
            raise ApiProblem(
                "stripe_resource_invalid", 409, "The selected Sandbox resources are invalid."
            )
        if (
            stripe_price.get("id") != mapping.stripe_price_id
            or stripe_price.get("product") != mapping.stripe_product_id
            or stripe_price.get("active") is not True
            or stripe_price.get("type") != "one_time"
            or stripe_price.get("unit_amount") != product.price_cents
            or str(stripe_price.get("currency", "")).lower() != product.currency.lower()
        ):
            raise ApiProblem(
                "stripe_resource_invalid", 409, "The selected Sandbox resources are invalid."
            )
        if stripe_price.get("recurring") is not None:
            raise ApiProblem(
                "stripe_resource_invalid", 409, "The selected price is not a one-time price."
            )

    def _reserve_order(
        self,
        product: Product,
        mapping: StripeCatalogueMapping,
        account_id: str,
        idempotency_key: str,
        fingerprint: str,
    ) -> Order | None:
        self.db.rollback()
        try:
            with self.db.begin():
                order = Order(
                    user_id=self.user_id,
                    product_id=product.id,
                    sku_snapshot=product.sku,
                    name_snapshot=product.name,
                    price_cents=product.price_cents,
                    currency=product.currency.upper(),
                    gems=product.gems,
                    stripe_account_id=account_id,
                    stripe_product_id=mapping.stripe_product_id,
                    stripe_price_id=mapping.stripe_price_id,
                    idempotency_key=idempotency_key,
                    request_fingerprint=fingerprint,
                )
                self.db.add(order)
                self.db.flush()
                return order
        except IntegrityError:
            self.db.rollback()
            return None

    def _ensure_customer(self, gateway: StripeGateway, account_id: str) -> str:
        self.db.rollback()
        created_here = False
        mapping = self.db.execute(
            select(StripeCustomerMapping).where(
                StripeCustomerMapping.user_id == self.user_id,
                StripeCustomerMapping.stripe_account_id == account_id,
            )
        ).scalar_one_or_none()
        self.db.rollback()
        if mapping is None:
            creation_key = _customer_idempotency_key(self.user_id, account_id)
            try:
                with self.db.begin():
                    mapping = StripeCustomerMapping(
                        user_id=self.user_id,
                        stripe_account_id=account_id,
                        creation_status="creating",
                        creation_idempotency_key=creation_key,
                    )
                    self.db.add(mapping)
                    self.db.flush()
                    created_here = True
            except IntegrityError:
                self.db.rollback()
                mapping = self.db.execute(
                    select(StripeCustomerMapping).where(
                        StripeCustomerMapping.user_id == self.user_id,
                        StripeCustomerMapping.stripe_account_id == account_id,
                    )
                ).scalar_one_or_none()
                if mapping is None:
                    raise ApiProblem(
                        "customer_recovery_required",
                        503,
                        "The Stripe customer mapping requires recovery.",
                    ) from None
        if mapping.creation_status == "unknown":
            raise ApiProblem(
                "customer_recovery_required", 409, "The Stripe customer mapping requires recovery."
            )
        if mapping.stripe_customer_id:
            return self._validate_customer(gateway, mapping.stripe_customer_id)
        if not created_here:
            raise ApiProblem(
                "customer_creation_in_progress", 409, "The Stripe customer is still being created."
            )
        try:
            customer = gateway.create_customer({}, mapping.creation_idempotency_key)
            customer_id = _validate_resource(customer, "customer", "customer creation")
            if _is_live(customer):
                raise ApiProblem(
                    "stripe_resource_invalid", 409, "A live Stripe customer was returned."
                )
            self.db.rollback()
            with self.db.begin():
                stored = self.db.execute(
                    select(StripeCustomerMapping)
                    .where(StripeCustomerMapping.id == mapping.id)
                    .with_for_update()
                ).scalar_one()
                stored.stripe_customer_id = customer_id
                stored.creation_status = "ready"
            return customer_id
        except ApiProblem:
            self._mark_customer_unknown(mapping.id)
            raise
        except StripeClientError:
            self._mark_customer_unknown(mapping.id)
            raise ApiProblem(
                "customer_recovery_required", 503, "The Stripe customer could not be confirmed."
            ) from None

    def _validate_customer(self, gateway: StripeGateway, customer_id: str) -> str:
        try:
            customer = gateway.retrieve_customer(customer_id)
        except StripeClientError:
            raise ApiProblem(
                "stripe_unavailable", 503, "The Stripe customer cannot be verified."
            ) from None
        if _is_live(customer) or customer.get("id") != customer_id:
            raise ApiProblem(
                "stripe_resource_invalid", 409, "The Stripe customer is invalid for this Sandbox."
            )
        return customer_id

    def _mark_customer_unknown(self, mapping_id: UUID) -> None:
        self.db.rollback()
        try:
            with self.db.begin():
                mapping = self.db.execute(
                    select(StripeCustomerMapping)
                    .where(StripeCustomerMapping.id == mapping_id)
                    .with_for_update()
                ).scalar_one_or_none()
                if mapping is not None and mapping.creation_status != "ready":
                    mapping.creation_status = "unknown"
        except Exception:
            self.db.rollback()

    def _mark_order_creating(self, order_id: UUID) -> None:
        self.db.rollback()
        with self.db.begin():
            order = self.db.execute(
                select(Order).where(Order.id == order_id).with_for_update()
            ).scalar_one()
            if order.checkout_session_id:
                return
            if order.checkout_status == "unknown":
                raise ApiProblem(
                    "checkout_recovery_required", 409, "The checkout attempt requires recovery."
                )
            if order.checkout_status == "creating":
                raise ApiProblem(
                    "checkout_in_progress", 409, "The checkout request is already in progress."
                )
            order.checkout_status = "creating"

    def _mark_order_unknown(self, order_id: UUID) -> None:
        self.db.rollback()
        try:
            with self.db.begin():
                order = self.db.execute(
                    select(Order).where(Order.id == order_id).with_for_update()
                ).scalar_one_or_none()
                if order is not None and order.checkout_session_id is None:
                    order.checkout_status = "unknown"
        except Exception:
            self.db.rollback()

    def _existing_checkout(
        self, order: Order, gateway: StripeGateway, account_id: str
    ) -> CheckoutResult:
        self._assert_order_account(order, account_id)
        self._validate_snapshot(order, gateway)
        try:
            session = gateway.retrieve_checkout_session(order.checkout_session_id or "")
            checkout_url = _validate_checkout_session(
                session,
                order,
                None,
                require_unpaid=False,
            )
        except ApiProblem:
            raise
        except StripeClientError:
            raise ApiProblem(
                "checkout_recovery_required",
                503,
                "The existing checkout session could not be recovered.",
            ) from None
        self._refresh_from_normalized_session(order, session, gateway)
        self.db.refresh(order)
        return CheckoutResult(order, checkout_url)

    def _refresh_from_session(self, order: Order, gateway: StripeGateway) -> None:
        try:
            session = gateway.retrieve_checkout_session(order.checkout_session_id or "")
            _validate_checkout_session(
                session,
                order,
                None,
                require_unpaid=False,
            )
        except ApiProblem:
            raise
        except StripeClientError:
            raise ApiProblem(
                "stripe_unavailable", 503, "The payment status cannot be verified now."
            ) from None
        self._refresh_from_normalized_session(order, session, gateway)

    def _refresh_from_normalized_session(
        self, order: Order, session: dict[str, Any], gateway: StripeGateway
    ) -> None:
        try:
            items = list(gateway.list_checkout_session_line_items(order.checkout_session_id or ""))
        except StripeClientError:
            raise ApiProblem(
                "stripe_unavailable", 503, "The payment status cannot be verified now."
            ) from None
        if len(items) != 1:
            raise ApiProblem(
                "payment_verification_failed", 409, "The Checkout Session does not match the order."
            )
        item = items[0]
        price = item.get("price")
        price_id = price.get("id") if isinstance(price, dict) else price
        if price_id != order.stripe_price_id or item.get("quantity") != 1:
            raise ApiProblem(
                "payment_verification_failed", 409, "The Checkout Session does not match the order."
            )
        payment_status = str(session.get("payment_status") or "unpaid")
        session_status = session.get("status")
        if session_status == "expired":
            order_status = "expired"
        elif session_status == "complete" and payment_status == "paid":
            order_status = "paid"
        else:
            order_status = "pending"
        self.db.rollback()
        with self.db.begin():
            stored = self.db.execute(
                select(Order).where(Order.id == order.id).with_for_update()
            ).scalar_one()
            stored.status = order_status
            stored.payment_status = payment_status[:32]
            stored.payment_intent_id = _resource_id(session.get("payment_intent"))
            stored.session_expires_at = (
                _timestamp_datetime(session.get("expires_at")) or stored.session_expires_at
            )
            stored.checkout_status = "created"

    def _validate_snapshot(self, order: Order, gateway: StripeGateway) -> None:
        mapping = StripeCatalogueMapping(
            product_id=order.product_id,
            stripe_account_id=order.stripe_account_id,
            stripe_product_id=order.stripe_product_id,
            stripe_price_id=order.stripe_price_id,
            catalogue_version=CATALOGUE_VERSION,
        )
        product = Product(
            sku=order.sku_snapshot,
            name=order.name_snapshot,
            product_type="one_time",
            price_cents=order.price_cents,
            currency=order.currency,
            gems=order.gems,
        )
        self._validate_mapping_resources(mapping, product, gateway)

    def _assert_order_account(self, order: Order, account_id: str) -> None:
        if order.stripe_account_id != account_id:
            raise ApiProblem(
                "stripe_resource_invalid", 409, "The order belongs to another Sandbox."
            )

    def _assert_idempotency_compatible(self, order: Order, fingerprint: str) -> None:
        if order.user_id != self.user_id or order.request_fingerprint != fingerprint:
            raise ApiProblem(
                "idempotency_conflict", 409, "The idempotency key is bound to another request."
            )

    def _session_params(
        self, order: Order, customer_id: str, expires_at: datetime
    ) -> dict[str, Any]:
        base = self.settings.frontend_base_url
        return {
            "mode": "payment",
            "customer": customer_id,
            "line_items": [{"price": order.stripe_price_id, "quantity": 1}],
            "success_url": (
                f"{base}/billing/success?order={order.id}&session_id={{CHECKOUT_SESSION_ID}}"
            ),
            "cancel_url": f"{base}/billing/cancel?order={order.id}",
            "client_reference_id": str(order.id),
            "metadata": {"nexusai_order_id": str(order.id)},
            "expires_at": int(expires_at.timestamp()),
            "allow_promotion_codes": False,
            "adaptive_pricing": {"enabled": False},
        }


def _fingerprint(sku: str) -> str:
    return hashlib.sha256(sku.encode("utf-8")).hexdigest()


def _customer_idempotency_key(user_id: UUID, account_id: str) -> str:
    digest = hashlib.sha256(f"{account_id}:{user_id}".encode()).hexdigest()
    return f"nexusai-customer-{digest}"


def _is_live(resource: dict[str, Any]) -> bool:
    return resource.get("livemode") is True


def _resource_id(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("id"), str):
        return value["id"]
    return None


def _validate_resource(resource: dict[str, Any], expected: str, operation: str) -> str:
    if resource.get("object") != expected:
        raise ApiProblem(
            "stripe_resource_invalid", 409, f"The Stripe {operation} response is invalid."
        )
    value = resource.get("id")
    if not isinstance(value, str) or not value:
        raise ApiProblem(
            "stripe_resource_invalid", 409, f"The Stripe {operation} response is invalid."
        )
    return value


def _timestamp_datetime(value: Any) -> datetime | None:
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, UTC)
    return None


def _validate_checkout_session(
    session: dict[str, Any],
    order: Order,
    customer_id: str | None,
    *,
    require_unpaid: bool,
) -> str:
    session_id = _validate_resource(session, "checkout.session", "Checkout Session")
    if not session_id.startswith("cs_test_") or _is_live(session):
        raise ApiProblem(
            "stripe_resource_invalid", 409, "A live or malformed Checkout Session was returned."
        )
    expected_customer = customer_id or _resource_id(session.get("customer"))
    metadata = session.get("metadata")
    if not isinstance(metadata, dict):
        raise ApiProblem(
            "payment_verification_failed", 409, "The Checkout Session does not match the order."
        )
    if (
        session.get("mode") != "payment"
        or session.get("client_reference_id") != str(order.id)
        or metadata.get("nexusai_order_id") != str(order.id)
        or _resource_id(session.get("customer")) != (expected_customer or order.stripe_customer_id)
        or session.get("amount_total") != order.price_cents
        or str(session.get("currency", "")).lower() != order.currency.lower()
    ):
        raise ApiProblem(
            "payment_verification_failed", 409, "The Checkout Session does not match the order."
        )
    if require_unpaid and session.get("payment_status") not in {None, "unpaid"}:
        raise ApiProblem(
            "payment_verification_failed", 409, "The new Checkout Session is already settled."
        )
    url = session.get("url")
    try:
        parsed = urlparse(url) if isinstance(url, str) else None
        parsed_port = parsed.port if parsed is not None else None
    except ValueError:
        parsed = None
        parsed_port = None
    if (
        parsed is None
        or parsed.scheme != "https"
        or parsed.hostname != "checkout.stripe.com"
        or parsed.username
        or parsed.password
        or parsed_port is not None
        or not parsed.path
    ):
        raise ApiProblem("checkout_url_invalid", 503, "Stripe returned an invalid Checkout URL.")
    return url
