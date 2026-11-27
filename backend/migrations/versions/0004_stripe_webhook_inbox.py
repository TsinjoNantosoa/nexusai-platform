"""Add the durable Stripe webhook inbox and fulfillment states."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_stripe_webhook_inbox"
down_revision: str | None = "0003_checkout_orders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_orders_fulfillment_status", "orders", type_="check")
    op.create_check_constraint(
        "ck_orders_fulfillment_status",
        "orders",
        "fulfillment_status IN ('pending', 'processing', 'fulfilled', 'review', 'failed')",
    )
    op.create_table(
        "stripe_webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stripe_account_id", sa.String(length=64), nullable=False),
        sa.Column("stripe_event_id", sa.String(length=120), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("related_resource_id", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processing_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.CheckConstraint(
            "status IN ('received', 'processing', 'retry', 'completed', 'failed', 'review')",
            name="ck_stripe_webhook_event_status",
        ),
        sa.CheckConstraint("retry_count >= 0", name="ck_stripe_webhook_event_retry_count"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stripe_account_id", "stripe_event_id", name="uq_stripe_webhook_account_event"
        ),
    )
    op.create_index(
        "ix_stripe_webhook_event_queue",
        "stripe_webhook_events",
        ["status", "next_attempt_at", "received_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_stripe_webhook_event_queue", table_name="stripe_webhook_events")
    op.drop_table("stripe_webhook_events")
    op.drop_constraint("ck_orders_fulfillment_status", "orders", type_="check")
    op.create_check_constraint(
        "ck_orders_fulfillment_status",
        "orders",
        "fulfillment_status IN ('pending', 'fulfilled')",
    )
