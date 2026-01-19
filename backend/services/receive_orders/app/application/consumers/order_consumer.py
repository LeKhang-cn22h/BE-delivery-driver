import logging
from application.services.order_service import OrderService

logger = logging.getLogger(__name__)


class OrderConsumer:
    def __init__(self):
        self.order_service = OrderService()

    async def process_order_message(self, message_data: dict):
        """
        Xử lý message nhận được từ RabbitMQ
        Message format mong đợi:
        {
            "priority": "urgent" hoặc "normal",
            "customer_name": "...",
            "customer_phone": "...",
            "pickup_address": {...},
            "delivery_address": {...},
            "items": [...],
            "total_amount": 100000,
            "notes": "..."
        }
        """
        try:
            logger.info(f"🔄 Processing order: {message_data.get('customer_name')}")

            # Validate data
            required_fields = [
                "priority", "customer_name", "customer_phone",
                "pickup_address", "delivery_address", "items"
            ]

            for field in required_fields:
                if field not in message_data:
                    raise ValueError(f"Missing required field: {field}")

            # Tạo order thông qua service
            order = self.order_service.create_order(message_data)

            logger.info(
                f"✅ Order created successfully: "
                f"ID={order['id']}, Code={order['order_code']}"
            )

            # TODO: Có thể publish event confirmation ngược lại nếu cần
            # await rabbitmq_client.publish({
            #     "event": "order.created",
            #     "order_id": order["id"],
            #     "order_code": order["order_code"]
            # }, routing_key="order.created")

            return order

        except Exception as e:
            logger.error(f"❌ Failed to process order message: {e}")
            # TODO: Có thể gửi message vào Dead Letter Queue
            raise