from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApiProblem, DuplicateOperation
from app.db.models import AuditLog, Order, WebhookEvent, utcnow
from app.wallet.service import apply_movement

from .checkout import _resource_id, _validate_checkout_session
from .stripe_client import StripeClient, StripeClientError, StripeGateway


class RetryableWebhookError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code[:80]
        super().__init__(self.code)


class FinancialReviewError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code[:80]
        super().__init__(self.code)


@dataclass(frozen=True)
class PaymentEvidence:
    session_id: str
    payment_intent_id: str


class WebhookProcessor:
    supported_events = {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
        "checkout.session.async_payment_failed",
        "checkout.session.expired",
    }

    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def claim_next(self) -> UUID | None:
        now = utcnow()
        abandoned_before = now - timedelta(
            seconds=self.settings.stripe_webhook_processing_timeout_seconds
        )
        self.db.rollback()
        with self.db.begin():
            event = self.db.execute(
                select(WebhookEvent)
                .where(
                    or_(
                        WebhookEvent.status.in_(["received", "retry"]),
                        (
                            and_(
                                WebhookEvent.status == "processing",
                                WebhookEvent.processing_at < abandoned_before,
                            )
                        ),
                    ),
                    or_(
                        WebhookEvent.next_attempt_at.is_(None),
                        WebhookEvent.next_attempt_at <= now,
                    ),
                )
                .order_by(WebhookEvent.received_at, WebhookEvent.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            ).scalar_one_or_none()
            if event is None:
                return None
            event.status = "processing"
            event.processing_at = now
            event.retry_count += 1
            event.next_attempt_at = None
            return event.id

    def process_one(self, event_id: UUID) -> str:
        event = self._event(event_id)
        if event is None or event.status != "processing":
            return "skipped"
        try:
            if event.event_type not in self.supported_events:
                self._complete_event(event_id)
                return "unsupported"
            if not event.related_resource_id:
                raise FinancialReviewError("resource_id_missing")
            order = self._find_order(event)
            if order is None:
                raise FinancialReviewError("order_not_found")
            if order.stripe_account_id != event.stripe_account_id:
                raise FinancialReviewError("stripe_account_mismatch")
            gateway = self._gateway()
            if event.event_type in {
                "checkout.session.completed",
                "checkout.session.async_payment_succeeded",
            }:
                evidence = self.verify_paid_order(order, gateway)
                self._fulfill(event_id, order.id, evidence)
            else:
                self._process_nonpaid(event_id, order.id, gateway, event.event_type)
            return "completed"
        except FinancialReviewError as error:
            self._mark_review(event_id, error.code, event.related_resource_id)
            return "review"
        except (StripeClientError, RetryableWebhookError) as error:
            self._mark_retry(event_id, getattr(error, "code", "stripe_unavailable"))
            return "retry"
        except DuplicateOperation:
            self._mark_review(event_id, "duplicate_wallet_reference", event.related_resource_id)
            return "review"
        except Exception:
            self._mark_retry(event_id, "processing_error")
            return "retry"

    def verify_paid_order(self, order: Order, gateway: StripeGateway) -> PaymentEvidence:
        session_id = order.checkout_session_id
        if not session_id:
            raise FinancialReviewError("checkout_session_missing")
        try:
            session = dict(gateway.retrieve_checkout_session(session_id))
            _validate_checkout_session(
                session,
                order,
                order.stripe_customer_id,
                require_unpaid=False,
                require_url=False,
            )
            items = list(gateway.list_checkout_session_line_items(session_id))
        except StripeClientError:
            raise
        except ApiProblem:
            raise FinancialReviewError("checkout_session_mismatch") from None
        if session.get("status") != "complete" or session.get("payment_status") != "paid":
            raise FinancialReviewError("payment_not_paid")
        if len(items) != 1:
            raise FinancialReviewError("line_items_invalid")
        item = dict(items[0])
        if item.get("quantity") != 1 or not isinstance(item.get("price"), dict):
            raise FinancialReviewError("line_items_invalid")
        price = dict(item["price"])
        if price.get("id") != order.stripe_price_id:
            raise FinancialReviewError("price_mismatch")
        try:
            verified_price = dict(gateway.retrieve_price(order.stripe_price_id))
        except StripeClientError:
            raise
        if (
            verified_price.get("id") != order.stripe_price_id
            or verified_price.get("product") != order.stripe_product_id
            or verified_price.get("unit_amount") != order.price_cents
            or str(verified_price.get("currency", "")).lower() != order.currency.lower()
            or verified_price.get("type") != "one_time"
            or verified_price.get("recurring") is not None
            or verified_price.get("livemode") is True
        ):
            raise FinancialReviewError("price_verification_failed")
        payment_intent_id = _resource_id(session.get("payment_intent"))
        if not payment_intent_id:
            raise FinancialReviewError("payment_intent_missing")
        if order.payment_intent_id and order.payment_intent_id != payment_intent_id:
            raise FinancialReviewError("payment_intent_mismatch")
        try:
            payment_intent = dict(gateway.retrieve_payment_intent(payment_intent_id))
        except AttributeError:
            raise FinancialReviewError("payment_intent_gateway_missing") from None
        except StripeClientError:
            raise
        if (
            payment_intent.get("id") != payment_intent_id
            or payment_intent.get("object") != "payment_intent"
            or payment_intent.get("livemode") is True
            or payment_intent.get("status") != "succeeded"
            or payment_intent.get("amount_received", payment_intent.get("amount"))
            != order.price_cents
            or str(payment_intent.get("currency", "")).lower() != order.currency.lower()
            or _resource_id(payment_intent.get("customer")) != order.stripe_customer_id
        ):
            raise FinancialReviewError("payment_intent_verification_failed")
        return PaymentEvidence(session_id, payment_intent_id)

    def _gateway(self) -> StripeGateway:
        try:
            return StripeClient(self.settings)
        except StripeClientError as error:
            raise RetryableWebhookError(error.code) from None

    def _find_order(self, event: WebhookEvent) -> Order | None:
        self.db.rollback()
        if event.event_type.startswith("checkout.session"):
            return self.db.execute(
                select(Order).where(
                    Order.stripe_account_id == event.stripe_account_id,
                    Order.checkout_session_id == event.related_resource_id,
                )
            ).scalar_one_or_none()
        return None

    def _event(self, event_id: UUID) -> WebhookEvent | None:
        self.db.rollback()
        return self.db.execute(
            select(WebhookEvent).where(WebhookEvent.id == event_id)
        ).scalar_one_or_none()

    def _fulfill(self, event_id: UUID, order_id: UUID, evidence: PaymentEvidence) -> None:
        self.db.rollback()
        with self.db.begin():
            event = self.db.execute(
                select(WebhookEvent).where(WebhookEvent.id == event_id).with_for_update()
            ).scalar_one()
            order = self.db.execute(
                select(Order).where(Order.id == order_id).with_for_update()
            ).scalar_one()
            if order.fulfillment_status == "fulfilled":
                event.status = "completed"
                event.processed_at = utcnow()
                event.error_code = None
                return
            if order.status in {"failed", "canceled", "expired"}:
                raise FinancialReviewError("incompatible_order_state")
            order.status = "paid"
            order.payment_status = "paid"
            order.payment_intent_id = evidence.payment_intent_id
            order.fulfillment_status = "processing"
            reference = f"stripe_purchase:{order.stripe_account_id}:{evidence.payment_intent_id}"
            apply_movement(
                self.db,
                order.user_id,
                order.gems,
                "purchase",
                reference,
                metadata={
                    "order_id": str(order.id),
                    "stripe_event_id": event.stripe_event_id,
                    "stripe_payment_intent_id": evidence.payment_intent_id,
                },
            )
            order.fulfillment_status = "fulfilled"
            event.status = "completed"
            event.processed_at = utcnow()
            event.error_code = None

    def _process_nonpaid(
        self,
        event_id: UUID,
        order_id: UUID,
        gateway: StripeGateway,
        event_type: str,
    ) -> None:
        order = self.db.execute(select(Order).where(Order.id == order_id)).scalar_one()
        self.db.rollback()
        try:
            session = dict(gateway.retrieve_checkout_session(order.checkout_session_id or ""))
            _validate_checkout_session(
                session,
                order,
                order.stripe_customer_id,
                require_unpaid=False,
                require_url=False,
            )
        except StripeClientError:
            raise
        except ApiProblem:
            raise FinancialReviewError("checkout_session_mismatch") from None
        if session.get("payment_status") == "paid" or order.status == "paid":
            raise FinancialReviewError("paid_order_received_nonpaid_event")
        self.db.rollback()
        with self.db.begin():
            event = self.db.execute(
                select(WebhookEvent).where(WebhookEvent.id == event_id).with_for_update()
            ).scalar_one()
            stored = self.db.execute(
                select(Order).where(Order.id == order_id).with_for_update()
            ).scalar_one()
            if stored.status != "paid" and stored.fulfillment_status not in {"fulfilled", "review"}:
                stored.status = "failed" if event_type.endswith("failed") else "expired"
                stored.payment_status = "failed" if event_type.endswith("failed") else "unpaid"
            event.status = "completed"
            event.processed_at = utcnow()
            event.error_code = None

    def _complete_event(self, event_id: UUID) -> None:
        self.db.rollback()
        with self.db.begin():
            event = self.db.execute(
                select(WebhookEvent).where(WebhookEvent.id == event_id).with_for_update()
            ).scalar_one()
            event.status = "completed"
            event.processed_at = utcnow()
            event.error_code = None

    def _mark_retry(self, event_id: UUID, code: str) -> None:
        self.db.rollback()
        with self.db.begin():
            event = self.db.execute(
                select(WebhookEvent).where(WebhookEvent.id == event_id).with_for_update()
            ).scalar_one()
            if event.retry_count >= self.settings.stripe_webhook_max_retries:
                event.status = "failed"
                event.processed_at = utcnow()
            else:
                event.status = "retry"
                event.next_attempt_at = utcnow() + timedelta(
                    seconds=min(300, 2 ** max(0, event.retry_count - 1))
                )
            event.error_code = code[:80]

    def _mark_review(self, event_id: UUID, code: str, resource_id: str | None) -> None:
        self.db.rollback()
        with self.db.begin():
            event = self.db.execute(
                select(WebhookEvent).where(WebhookEvent.id == event_id).with_for_update()
            ).scalar_one()
            event.status = "review"
            event.processed_at = utcnow()
            event.error_code = code[:80]
            if resource_id:
                order = self.db.execute(
                    select(Order)
                    .where(
                        Order.stripe_account_id == event.stripe_account_id,
                        Order.checkout_session_id == resource_id,
                    )
                    .with_for_update()
                ).scalar_one_or_none()
                if order is not None and order.fulfillment_status == "pending":
                    order.fulfillment_status = "review"


def requeue_event(session: Session, event_id: UUID) -> None:
    session.rollback()
    with session.begin():
        event = session.execute(
            select(WebhookEvent).where(WebhookEvent.id == event_id).with_for_update()
        ).scalar_one_or_none()
        if event is None:
            raise ApiProblem("webhook_event_not_found", 404, "Webhook event not found.")
        if event.status not in {"failed", "review"}:
            raise ApiProblem("webhook_replay_invalid", 409, "Only terminal events can be replayed.")
        event.status = "retry"
        event.next_attempt_at = utcnow()
        event.error_code = None
        session.add(
            AuditLog(
                action="stripe_webhook_replay_requested",
                entity_type="stripe_webhook_event",
                entity_id=str(event.id),
                metadata_json={"stripe_event_id": event.stripe_event_id},
            )
        )
