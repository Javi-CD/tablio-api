"""create orders and order_items

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE order_status AS ENUM "
        "('pending', 'accepted', 'preparing', 'completed', 'cancelled')"
    )
    op.execute("CREATE TYPE order_type AS ENUM ('table', 'delivery', 'pickup')")

    op.create_table(
        "orders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("restaurant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("customer_phone", sa.String(50), nullable=True),
        sa.Column("customer_notes", sa.Text(), nullable=True),
        sa.Column("table_number", sa.String(20), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "accepted",
                "preparing",
                "completed",
                "cancelled",
                name="order_status",
                create_type=False,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "order_type",
            postgresql.ENUM(
                "table",
                "delivery",
                "pickup",
                name="order_type",
                create_type=False,
            ),
            server_default="table",
            nullable=False,
        ),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orders_restaurant_id", "orders", ["restaurant_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])

    op.create_table(
        "order_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "quantity", sa.Integer(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_restaurant_id", table_name="orders")
    op.drop_table("orders")
    op.execute("DROP TYPE order_type")
    op.execute("DROP TYPE order_status")
