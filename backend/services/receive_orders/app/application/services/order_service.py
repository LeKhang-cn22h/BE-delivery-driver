# app/application/services/order_service.py
from domain.repositories.order_repository import OrderRepository
from infrastructure.messaging.kafka_producer import send_event
from datetime import datetime

import redis
import json
import os


class OrderService:
    def __init__(self):
        self.repository = OrderRepository()
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )

    # def create_order(self, order_data: dict):
    #     # 1. Lưu vào Supabase (schema receive_orders)
    #     order = self.repository.create(order_data)
    #
    #     if not order:
    #         raise Exception("Failed to create order")
    #
    #     # 2. Đẩy vào Redis Queue
    #     queue_name = f"{order['priority']}_queue"
    #     self.redis_client.lpush(queue_name, json.dumps({
    #         "order_id": order["id"],
    #         "order_code": order["order_code"],
    #         "priority": order["priority"],
    #         "created_at": str(order["created_at"])
    #     }))
    #
    #     # 3. Publish event
    #     self.redis_client.publish("new_order_channel", json.dumps({
    #         "order_id": order["id"],
    #         "order_code": order["order_code"],
    #         "priority": order["priority"]
    #     }))
    #
    #     return order
    def create_order(self, order_data: dict):
        # 1. Lưu vào Supabase (schema receive_orders)
        order = self.repository.create(order_data)

        if not order:
            raise Exception("Failed to create order")

        # 2. Đẩy vào Redis Queue
        queue_name = f"{order['priority']}_queue"
        self.redis_client.lpush(queue_name, json.dumps({
            "order_id": order["id"],
            "order_code": order["order_code"],
            "priority": order["priority"],
            "created_at": str(order["created_at"])
        }))

        # 3. Publish Redis event (giữ nguyên)
        self.redis_client.publish("new_order_channel", json.dumps({
            "order_id": order["id"],
            "order_code": order["order_code"],
            "priority": order["priority"]
        }))

        # 4. 🚀 Emit event sang Kafka (MỚI)
        kafka_event = {
            "event_type": "order_created",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "receive_orders_service",
            "data": order
        }

        send_event(
            topic="order.events",
            key=str(order["id"]),
            value=kafka_event
        )

        return order

    def get_pending_orders(self, priority: str = None):
        return self.repository.find_pending_by_priority(priority)

    # def update_order_status(self, order_id: str, status: str):
    #     return self.repository.update_status(order_id, status)
    def update_order_status(self, order_id: str, status: str):
        order = self.repository.update_status(order_id, status)

        # Emit Kafka event
        kafka_event = {
            "event_type": "order_status_updated",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "receive_orders_service",
            "data": {
                "order_id": order_id,
                "new_status": status
            }
        }

        send_event(
            topic="order.events",
            key=str(order_id),
            value=kafka_event
        )

        return order
