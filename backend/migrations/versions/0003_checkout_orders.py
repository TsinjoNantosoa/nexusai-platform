"""Persist Stripe customers and hosted Checkout orders."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_checkout_orders"
down_revision: str | None = "0002_stripe_catalogue_mappings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stripe_customer_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stripe_account_id", sa.String(length=64), nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=120), nullable=True),
        sa.Column("creation_status", sa.String(length=16), nullable=False),
        sa.Column("creation_idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "creation_status IN ('creating', 'ready', 'unknown')",
            name="ck_stripe_customer_creation_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "stripe_account_id", name="uq_stripe_customer_user_account"),
        sa.UniqueConstraint(
            "stripe_account_id", "stripe_customer_id", name="uq_stripe_customer_account_id"
        ),
    )
    op.create_index(
        "ix_stripe_customer_account_user",
        "stripe_customer_mappings",
        ["stripe_account_id", "user_id"],
    )

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku_snapshot", sa.String(length=32), nullable=False),
        sa.Column("name_snapshot", sa.String(length=80), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("gems", sa.Integer(), nullable=False),
        sa.Column("stripe_account_id", sa.String(length=64), nullable=False),
        sa.Column("stripe_product_id", sa.String(length=120), nullable=False),
        sa.Column("stripe_price_id", sa.String(length=120), nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=120), nullable=True),
        sa.Column("checkout_session_id", sa.String(length=120), nullable=True),
        sa.Column("payment_intent_id", sa.String(length=120), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("checkout_status", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("payment_status", sa.String(length=32), nullable=False),
        sa.Column("fulfillment_status", sa.String(length=16), nullable=False),
        sa.Column("session_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("price_cents > 0", name="ck_orders_positive_price"),
        sa.CheckConstraint("gems > 0", name="ck_orders_positive_gems"),
        sa.CheckConstraint(
            "checkout_status IN ('pending', 'creating', 'created', 'unknown')",
            name="ck_orders_checkout_status",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'paid', 'failed', 'canceled', 'expired')",
            name="ck_orders_status",
        ),
        sa.CheckConstraint(
            "fulfillment_status IN ('pending', 'fulfilled')",
            name="ck_orders_fulfillment_status",
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
        sa.UniqueConstraint(
            "stripe_account_id", "checkout_session_id", name="uq_orders_account_checkout_session"
        ),
        sa.UniqueConstraint(
            "stripe_account_id", "payment_intent_id", name="uq_orders_account_payment_intent"
        ),
    )
    op.create_index("ix_orders_user_created", "orders", ["user_id", "created_at"])
    op.create_index("ix_orders_user_status", "orders", ["user_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_orders_user_status", table_name="orders")
    op.drop_index("ix_orders_user_created", table_name="orders")
    op.drop_table("orders")
    op.drop_index("ix_stripe_customer_account_user", table_name="stripe_customer_mappings")
    op.drop_table("stripe_customer_mappings")
