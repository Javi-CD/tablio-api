from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.order_item import OrderItem


class OrderStatus(str, enum.Enum):  # noqa: UP042
    PENDING = "pending"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderType(str, enum.Enum):  # noqa: UP042
    TABLE = "table"
    DELIVERY = "delivery"
    PICKUP = "pickup"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    customer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    table_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(
            OrderStatus,
            name="order_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
    )
    order_type: Mapped[OrderType] = mapped_column(
        SAEnum(
            OrderType,
            name="order_type",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=OrderType.TABLE,
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    items: Mapped[list[OrderItem]] = relationship(
        "OrderItem", back_populates="order", lazy="select"
    )
