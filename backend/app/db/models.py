from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="user")
    age_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    terms_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    wallet: Mapped["Wallet"] = relationship(back_populates="user", uselist=False)
    sessions: Mapped[list["SessionModel"]] = relationship(back_populates="user")

    __table_args__ = (CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),)


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    user: Mapped[User] = relationship(back_populates="sessions")

    __table_args__ = (Index("ix_sessions_user_active", "user_id", "revoked_at", "expires_at"),)


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    user: Mapped[User] = relationship(back_populates="wallet")
    entries: Mapped[list["WalletEntry"]] = relationship(back_populates="wallet")

    __table_args__ = (CheckConstraint("balance >= 0", name="ck_wallets_non_negative_balance"),)


class WalletEntry(Base):
    __tablename__ = "wallet_entries"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    wallet_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reference: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    original_reference: Mapped[str | None] = mapped_column(String(180))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    wallet: Mapped[Wallet] = relationship(back_populates="entries")

    __table_args__ = (
        CheckConstraint("amount <> 0", name="ck_wallet_entries_non_zero_amount"),
        Index("ix_wallet_entries_wallet_created", "wallet_id", "created_at"),
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    sku: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    product_type: Mapped[str] = mapped_column(String(16), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    gems: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    stripe_product_id: Mapped[str | None] = mapped_column(String(120))
    stripe_price_id: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint("price_cents >= 0", name="ck_products_non_negative_price"),
        CheckConstraint("gems >= 0", name="ck_products_non_negative_gems"),
        CheckConstraint(
            "product_type IN ('free', 'one_time', 'recurring')", name="ck_products_type"
        ),
    )


class StripeCatalogueMapping(Base):
    __tablename__ = "stripe_catalogue_mappings"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    stripe_account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    stripe_product_id: Mapped[str] = mapped_column(String(120), nullable=False)
    stripe_price_id: Mapped[str] = mapped_column(String(120), nullable=False)
    catalogue_version: Mapped[str] = mapped_column(String(64), nullable=False)
    synchronized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    product: Mapped[Product] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "stripe_account_id",
            "catalogue_version",
            name="uq_stripe_mapping_product_account_version",
        ),
        UniqueConstraint(
            "stripe_account_id",
            "stripe_product_id",
            "catalogue_version",
            name="uq_stripe_mapping_product_account_resource",
        ),
        UniqueConstraint(
            "stripe_account_id",
            "stripe_price_id",
            "catalogue_version",
            name="uq_stripe_mapping_price_account_resource",
        ),
        Index("ix_stripe_mapping_account_product", "stripe_account_id", "product_id"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(180))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (Index("ix_audit_logs_created", "created_at"),)
