"""Persist account-scoped Stripe catalogue mappings."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_stripe_catalogue_mappings"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stripe_catalogue_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stripe_account_id", sa.String(length=64), nullable=False),
        sa.Column("stripe_product_id", sa.String(length=120), nullable=False),
        sa.Column("stripe_price_id", sa.String(length=120), nullable=False),
        sa.Column("catalogue_version", sa.String(length=64), nullable=False),
        sa.Column("synchronized_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id",
            "stripe_account_id",
            "catalogue_version",
            name="uq_stripe_mapping_product_account_version",
        ),
        sa.UniqueConstraint(
            "stripe_account_id",
            "stripe_product_id",
            "catalogue_version",
            name="uq_stripe_mapping_product_account_resource",
        ),
        sa.UniqueConstraint(
            "stripe_account_id",
            "stripe_price_id",
            "catalogue_version",
            name="uq_stripe_mapping_price_account_resource",
        ),
    )
    op.create_index(
        "ix_stripe_mapping_account_product",
        "stripe_catalogue_mappings",
        ["stripe_account_id", "product_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_stripe_mapping_account_product", table_name="stripe_catalogue_mappings")
    op.drop_table("stripe_catalogue_mappings")
