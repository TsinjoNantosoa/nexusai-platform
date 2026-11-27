from __future__ import annotations

import argparse
import os
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import ApiProblem
from app.db.models import AuditLog, Order, WebhookEvent, utcnow
from app.db.session import build_engine, build_session_factory

from .fulfillment import WebhookProcessor
from .stripe_client import StripeClient


def historical_candidates(session: Session) -> list[Order]:
    return list(
        session.execute(
            select(Order)
            .where(Order.status == "paid", Order.fulfillment_status == "pending")
            .order_by(Order.created_at, Order.id)
        ).scalars()
    )


def reconcile_one(
    session: Session,
    settings: Settings,
    order_id: UUID,
    *,
    apply: bool = False,
    owner_approved: bool = False,
) -> str:
    if apply and not owner_approved:
        raise ApiProblem(
            "reconciliation_approval_required",
            403,
            "Historical fulfillment requires explicit owner approval.",
        )
    order = session.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise ApiProblem("order_not_found", 404, "Order not found.")
    if order.status != "paid" or order.fulfillment_status != "pending":
        return "not_eligible"
    gateway = StripeClient(settings)
    processor = WebhookProcessor(session, settings)
    evidence = processor.verify_paid_order(order, gateway)
    if not apply:
        return f"verified:{evidence.payment_intent_id}"
    session.rollback()
    event = WebhookEvent(
        stripe_account_id=order.stripe_account_id,
        stripe_event_id=f"reconciliation_{order.id}",
        event_type="historical.reconciliation",
        related_resource_id=order.checkout_session_id,
        status="processing",
        processing_at=utcnow(),
        retry_count=1,
    )
    with session.begin():
        session.add(event)
        session.flush()
        session.add(
            AuditLog(
                action="stripe_historical_reconciliation_applied",
                entity_type="order",
                entity_id=str(order.id),
                metadata_json={"stripe_payment_intent_id": evidence.payment_intent_id},
            )
        )
    processor._fulfill(event.id, order.id, evidence)
    return "fulfilled"


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely reconcile selected paid Stripe orders.")
    parser.add_argument("--order-id", type=UUID)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    engine = build_engine(settings)
    factory = build_session_factory(engine)
    try:
        with factory() as session:
            if args.order_id is None:
                for order in historical_candidates(session):
                    print(order.id)
                return
            result = reconcile_one(
                session,
                settings,
                args.order_id,
                apply=args.apply,
                owner_approved=(
                    settings.environment == "development"
                    and os.environ.get("NEXUSAI_RECONCILIATION_APPROVED") == "true"
                ),
            )
            print(result)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
