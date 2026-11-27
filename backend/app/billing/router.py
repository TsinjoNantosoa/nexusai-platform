from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import current_user, require_csrf
from app.core.config import Settings, get_settings
from app.core.errors import ApiProblem
from app.core.rate_limit import SlidingWindowLimiter
from app.db.models import Order, Product, User
from app.db.session import get_db

from .checkout import CheckoutService
from .schemas import CheckoutIn, CheckoutOut, OrderOut, ProductOut
from .webhooks import router as webhook_router

router = APIRouter(prefix="/billing", tags=["billing"])
router.include_router(webhook_router)
_checkout_limiters: dict[tuple[int, int], SlidingWindowLimiter] = {}


def checkout_limiter(settings: Settings) -> SlidingWindowLimiter:
    key = (settings.checkout_rate_limit, settings.checkout_rate_window_seconds)
    limiter = _checkout_limiters.get(key)
    if limiter is None:
        limiter = SlidingWindowLimiter(*key)
        _checkout_limiters[key] = limiter
    return limiter


@router.get("/products", response_model=list[ProductOut])
def products(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    rows = list(
        db.execute(
            select(Product).where(Product.active.is_(True)).order_by(Product.price_cents)
        ).scalars()
    )
    return [
        {
            "sku": row.sku,
            "name": row.name,
            "price_cents": row.price_cents,
            "currency": row.currency,
            "gems": row.gems,
            "subscription": row.product_type == "recurring",
        }
        for row in rows
    ]


@router.get("/subscription")
def subscription(user: User = Depends(current_user)) -> dict[str, object]:
    return {"status": "free", "renewsAt": None, "cancelAtPeriodEnd": False}


@router.post("/checkout", response_model=CheckoutOut)
def checkout(
    payload: CheckoutIn,
    request: Request,
    _: None = Depends(require_csrf),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, object]:
    if (
        not idempotency_key
        or len(idempotency_key) > 255
        or any(ord(character) < 33 or ord(character) > 126 for character in idempotency_key)
    ):
        raise ApiProblem("idempotency_key_invalid", 422, "A valid idempotency key is required.")
    host = request.client.host if request.client else "unknown"
    if not checkout_limiter(settings).allow(f"{host}:{user.id}"):
        raise ApiProblem("rate_limited", 429, "Too many checkout attempts.")
    result = CheckoutService(db, settings, user).create(payload.sku, idempotency_key)
    return {"order_id": result.order.id, "checkout_url": result.checkout_url}


@router.get("/orders", response_model=list[OrderOut])
def orders(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[dict[str, object]]:
    return [_order_payload(order) for order in CheckoutService(db, settings, user).list_orders()]


@router.get("/orders/{order_id}", response_model=OrderOut)
def order_status(
    order_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    try:
        parsed_id = UUID(order_id)
    except ValueError:
        raise ApiProblem("order_not_found", 404, "Order not found.") from None
    return _order_payload(CheckoutService(db, settings, user).get(parsed_id))


def _order_payload(order: Order) -> dict[str, object]:
    return {
        "id": order.id,
        "sku": order.sku_snapshot,
        "status": order.status,
        "payment_status": order.payment_status,
        "fulfillment_status": order.fulfillment_status,
        "gems": order.gems,
        "price_cents": order.price_cents,
        "currency": order.currency,
        "created_at": order.created_at,
    }


@router.post("/portal")
def portal(
    request: Request,
    _: None = Depends(require_csrf),
    user: User = Depends(current_user),
) -> None:
    raise ApiProblem("integration_pending", 501, "Stripe Customer Portal is reserved for Phase 3.")
