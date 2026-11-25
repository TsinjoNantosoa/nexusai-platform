from contextlib import nullcontext
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiProblem, DuplicateOperation, InsufficientBalance
from app.db.models import User, Wallet, WalletEntry


def _transaction(session: Session):
    return nullcontext() if session.in_transaction() else session.begin()


def create_initial_wallet(session: Session, user: User) -> Wallet:
    wallet = Wallet(user_id=user.id, balance=20)
    session.add(wallet)
    session.flush()
    session.add(
        WalletEntry(
            wallet_id=wallet.id,
            amount=20,
            entry_type="welcome",
            reference=f"welcome:{user.id}",
            metadata_json={"reason": "registration_bonus"},
        )
    )
    return wallet


def _locked_wallet(session: Session, user_id: UUID) -> Wallet:
    wallet = session.execute(
        select(Wallet).where(Wallet.user_id == user_id).with_for_update()
    ).scalar_one_or_none()
    if wallet is None:
        raise ApiProblem("wallet_not_found", 404, "Wallet not found.")
    return wallet


def _existing_entry(session: Session, reference: str) -> WalletEntry | None:
    return session.execute(
        select(WalletEntry).where(WalletEntry.reference == reference)
    ).scalar_one_or_none()


def _ensure_reference_available(
    entry: WalletEntry | None,
    wallet_id: UUID,
    amount: int,
    entry_type: str,
    original_reference: str | None,
) -> WalletEntry | None:
    if entry is None:
        return None
    if (
        entry.wallet_id != wallet_id
        or entry.amount != amount
        or entry.entry_type != entry_type
        or entry.original_reference != original_reference
    ):
        raise DuplicateOperation()
    return entry


def apply_movement(
    session: Session,
    user_id: UUID,
    amount: int,
    entry_type: str,
    reference: str,
    original_reference: str | None = None,
    metadata: dict[str, object] | None = None,
) -> WalletEntry:
    if amount == 0:
        raise ApiProblem("invalid_wallet_amount", 422, "Wallet movements cannot be zero.")
    with _transaction(session):
        wallet = _locked_wallet(session, user_id)
        existing = _ensure_reference_available(
            _existing_entry(session, reference), wallet.id, amount, entry_type, original_reference
        )
        if existing is not None:
            return existing
        if wallet.balance + amount < 0:
            raise InsufficientBalance()
        wallet.balance += amount
        entry = WalletEntry(
            wallet_id=wallet.id,
            amount=amount,
            entry_type=entry_type,
            reference=reference,
            original_reference=original_reference,
            metadata_json=metadata or {},
        )
        session.add(entry)
        session.flush()
        return entry


def refund_movement(
    session: Session,
    user_id: UUID,
    original_reference: str,
    amount: int,
    reference: str,
) -> WalletEntry:
    if amount <= 0:
        raise ApiProblem("invalid_refund_amount", 422, "Refund amount must be positive.")
    with _transaction(session):
        wallet = _locked_wallet(session, user_id)
        existing = _ensure_reference_available(
            _existing_entry(session, reference),
            wallet.id,
            amount,
            "restitution",
            original_reference,
        )
        if existing is not None:
            return existing
        original = session.execute(
            select(WalletEntry).where(
                WalletEntry.wallet_id == wallet.id,
                WalletEntry.reference == original_reference,
                WalletEntry.amount < 0,
            )
        ).scalar_one_or_none()
        if original is None:
            raise ApiProblem(
                "original_operation_not_found", 404, "The original debit was not found."
            )
        refunded = session.execute(
            select(func.coalesce(func.sum(WalletEntry.amount), 0)).where(
                WalletEntry.wallet_id == wallet.id,
                WalletEntry.original_reference == original_reference,
                WalletEntry.entry_type == "restitution",
            )
        ).scalar_one()
        if int(refunded) + amount > abs(original.amount):
            raise ApiProblem("refund_exceeds_debit", 409, "The refund exceeds the original debit.")
        wallet.balance += amount
        entry = WalletEntry(
            wallet_id=wallet.id,
            amount=amount,
            entry_type="restitution",
            reference=reference,
            original_reference=original_reference,
            metadata_json={"reason": "compensation"},
        )
        session.add(entry)
        session.flush()
        return entry
