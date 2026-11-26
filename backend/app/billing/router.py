from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import current_user, require_csrf
from app.core.errors import ApiProblem
from app.db.models import Product, User
from app.db.session import get_db

from .schemas import CheckoutIn, ProductOut

router = APIRouter(prefix="/billing", tags=["billing"])


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


@router.post("/checkout")
def checkout(
    payload: CheckoutIn,
    request: Request,
    _: None = Depends(require_csrf),
    user: User = Depends(current_user),
) -> None:
    raise ApiProblem("integration_pending", 501, "Stripe Checkout is reserved for Phase 3.")


@router.post("/portal")
def portal(
    request: Request,
    _: None = Depends(require_csrf),
    user: User = Depends(current_user),
) -> None:
    raise ApiProblem("integration_pending", 501, "Stripe Customer Portal is reserved for Phase 3.")
