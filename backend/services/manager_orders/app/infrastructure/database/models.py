import uuid
from sqlalchemy import (
    Column, String, Numeric, Boolean,
    ForeignKey, DateTime, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .session import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    pickup_point = Column(Text)
    status = Column(String(30), default="pending")
    is_urgent = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class OrderDetail(Base):
    __tablename__ = "order_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"))
    start_point = Column(Text)
    price = Column(Numeric(10, 2))
    status = Column(String(30), default="pending")


class OrderDetailUrgent(Base):
    __tablename__ = "order_detail_urgent"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_detail_id = Column(
        UUID(as_uuid=True),
        ForeignKey("order_details.id", ondelete="CASCADE")
    )
    start_point = Column(Text)
    urgent_time = Column(String)
    status = Column(String(30))
    price = Column(Numeric(10, 2))
