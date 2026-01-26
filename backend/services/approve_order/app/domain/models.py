# import uuid
# from sqlalchemy import (
#     Column, String, Integer, Date, DateTime, Boolean, ForeignKey, Numeric
# )
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.sql import func
# from infrastructure.database import Base


# class Order(Base):
#     __tablename__ = "orders"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     user_id = Column(UUID(as_uuid=True))
#     pickup_point = Column(String)
#     status = Column(String)
#     created_at = Column(DateTime, server_default=func.now())


# class OrderDetail(Base):
#     __tablename__ = "order_details"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
#     start_point = Column(String)
#     price = Column(Numeric)
#     status = Column(String)
#     address_detail = Column(String)
#     area_code = Column(String)
#     priority_score = Column(Integer)


# class Driver(Base):
#     __tablename__ = "drivers"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     user_id = Column(UUID(as_uuid=True))
#     name = Column(String)
#     phone = Column(String)
#     status = Column(String)
#     created_at = Column(DateTime, server_default=func.now())


# class Schedule(Base):
#     __tablename__ = "schedules"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"))
#     scheduled_date = Column(Date)
#     area_code = Column(String)
#     status = Column(String)
#     total_orders = Column(Integer)
#     completed_orders = Column(Integer, default=0)
#     failed_orders = Column(Integer, default=0)
#     created_at = Column(DateTime, server_default=func.now())


# class ScheduleItem(Base):
#     __tablename__ = "schedule_items"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     schedule_id = Column(UUID(as_uuid=True), ForeignKey("schedules.id"))
#     order_detail_id = Column(UUID(as_uuid=True), ForeignKey("order_details.id"))
#     status = Column(String)
#     queue = Column(Integer)
