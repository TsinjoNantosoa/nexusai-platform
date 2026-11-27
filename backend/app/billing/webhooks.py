from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import stripe
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import ApiProblem
from app.db.models import Order, WebhookEvent
from app.db.session import get_db

from .stripe_client import normalize_stripe_value

router = APIRouter(prefix="/webhooks", tags=["billing-webhooks"])


def _event_mapping(event: Any) -> dict[str, Any]:
    normalized = normalize_stripe_value(event)
    if not isinstance(normalized, dict):
        raise ValueError("event_not_object")
    return normalized


def _resource_id(event: Mapping[str, Any]) -> str | None:
    data = event.get("data")
    if not isinstance(data, Mapping):
        return None
    resource = data.get("object")
    if not isinstance(resource, Mapping):
        return None
    value = resource.get("id")
    return value if isinstance(value, str) and value else None


def _event_account(event: Mapping[str, Any]) -> str | None:
    account = event.get("account")
    return account if isinstance(account, str) and account.startswith("acct_") else None


def _configured_account(
    db: Session, settings: Settings, event: Mapping[str, Any], resource_id: str | None
) -> str:
    event_account = _event_account(event)
    if settings.stripe_account_id:
        if event_account and event_account != settings.stripe_account_id:
            raise ApiProblem("stripe_account_mismatch", 400, "Webhook account is not authorized.")
        return settings.stripe_account_id
    if resource_id:
        order = db.execute(
            select(Order).where(Order.checkout_session_id == resource_id)
        ).scalar_one_or_none()
        if order is not None:
            if event_account and event_account != order.stripe_account_id:
                raise ApiProblem(
                    "stripe_account_mismatch", 400, "Webhook account is not authorized."
                )
            return order.stripe_account_id
    raise ApiProblem(
        "stripe_account_unconfigured",
        503,
        "The Stripe Sandbox account is not configured for webhook intake.",
    )


def enqueue_event(
    db: Session, settings: Settings, payload: bytes, signature: str | None
) -> tuple[WebhookEvent, bool]:
    if not settings.stripe_enabled or settings.stripe_webhook_secret is None:
        raise ApiProblem("stripe_webhooks_disabled", 503, "Stripe webhooks are unavailable.")
    if not signature:
        raise ApiProblem("stripe_signature_missing", 400, "The Stripe signature is invalid.")
    try:
        parsed = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.stripe_webhook_secret.get_secret_value(),
            tolerance=settings.stripe_webhook_tolerance_seconds,
        )
        event = _event_mapping(parsed)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise ApiProblem(
            "stripe_signature_invalid", 400, "The Stripe signature is invalid."
        ) from None
    event_id = event.get("id")
    event_type = event.get("type")
    if (
        not isinstance(event_id, str)
        or not event_id.startswith("evt_")
        or not isinstance(event_type, str)
        or not event_type
        or event.get("livemode") is not False
    ):
        raise ApiProblem("stripe_event_invalid", 400, "The Stripe event is invalid.")
    resource_id = _resource_id(event)
    db.rollback()
    account_id = _configured_account(db, settings, event, resource_id)
    existing = db.execute(
        select(WebhookEvent).where(
            WebhookEvent.stripe_account_id == account_id,
            WebhookEvent.stripe_event_id == event_id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing, True
    db.rollback()
    try:
        with db.begin():
            stored = WebhookEvent(
                stripe_account_id=account_id,
                stripe_event_id=event_id,
                event_type=event_type,
                related_resource_id=resource_id,
                status="received",
            )
            db.add(stored)
            db.flush()
            return stored, False
    except IntegrityError:
        db.rollback()
        existing = db.execute(
            select(WebhookEvent).where(
                WebhookEvent.stripe_account_id == account_id,
                WebhookEvent.stripe_event_id == event_id,
            )
        ).scalar_one_or_none()
        if existing is None:
            raise ApiProblem(
                "webhook_persistence_failed", 503, "The webhook could not be accepted."
            ) from None
        return existing, True
    except Exception:
        db.rollback()
        raise ApiProblem(
            "webhook_persistence_failed", 503, "The webhook could not be accepted."
        ) from None


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    content_length = request.headers.get("content-length")
    if (
        content_length
        and content_length.isdigit()
        and int(content_length) > settings.stripe_webhook_max_body_bytes
    ):
        raise ApiProblem("stripe_payload_too_large", 413, "The webhook payload is too large.")
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > settings.stripe_webhook_max_body_bytes:
            raise ApiProblem("stripe_payload_too_large", 413, "The webhook payload is too large.")
        chunks.append(chunk)
    try:
        _stored, duplicate = enqueue_event(
            db,
            settings,
            b"".join(chunks),
            request.headers.get("Stripe-Signature"),
        )
    except ApiProblem:
        raise
    except Exception:
        raise ApiProblem(
            "webhook_persistence_failed", 503, "The webhook could not be accepted."
        ) from None
    return JSONResponse(
        status_code=200,
        content={"accepted": True, "duplicate": duplicate, "request_id": request.state.request_id},
        headers={"X-Request-ID": request.state.request_id},
    )
