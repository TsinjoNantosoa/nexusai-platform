from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import current_user
from app.core.errors import ApiProblem
from app.db.models import User, Wallet, WalletEntry
from app.db.session import get_db

from .schemas import EntryOut, WalletOut

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("", response_model=WalletOut)
def wallet(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    record = db.execute(select(Wallet).where(Wallet.user_id == user.id)).scalar_one_or_none()
    if record is None:
        raise ApiProblem("wallet_not_found", 404, "Wallet not found.")
    return {"balance": record.balance, "inReview": False}


@router.get("/transactions", response_model=list[EntryOut])
def transactions(
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    wallet_id = db.execute(select(Wallet.id).where(Wallet.user_id == user.id)).scalar_one_or_none()
    if wallet_id is None:
        raise ApiProblem("wallet_not_found", 404, "Wallet not found.")
    rows = list(
        db.execute(
            select(WalletEntry)
            .where(WalletEntry.wallet_id == wallet_id)
            .order_by(desc(WalletEntry.created_at), desc(WalletEntry.id))
            .offset(offset)
            .limit(limit)
        ).scalars()
    )
    total = db.execute(
        select(func.count()).select_from(WalletEntry).where(WalletEntry.wallet_id == wallet_id)
    ).scalar_one()
    next_offset = offset + len(rows) if offset + len(rows) < total else ""
    response.headers["X-Next-Offset"] = str(next_offset)
    response.headers["X-Total-Count"] = str(total)
    return [
        {
            "id": row.id,
            "type": row.entry_type,
            "amount": row.amount,
            "reference": row.reference,
            "created_at": row.created_at,
            "status": "completed",
        }
        for row in rows
    ]
