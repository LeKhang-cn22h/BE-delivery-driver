#application/use_case/create_order.py
from domain.entities.order import Order, OrderStatus, DetailStatus
from domain.repositories.order_repository import OrderRepository
from domain.repositories.order_detail_repository import OrderDetailRepository
from domain.events.event_publisher import EventPublisher
from domain.events.order_created_event import OrderCreatedEvent



class CreateOrderUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        order_detail_repository: OrderDetailRepository,
        event_publisher: EventPublisher,
    ):
        self.order_repository = order_repository
        self.order_detail_repository = order_detail_repository
        self.event_publisher = event_publisher

    async def execute(self, order: Order) -> Order:
        order.validate()
        order.status = OrderStatus.pending

        for detail in order.order_details:
            detail.status = DetailStatus.pending

        created_order = await self.order_repository.create(order)

        for detail in order.order_details:
            detail.order_id = created_order.id

        created_details = await self.order_detail_repository.create_batch(
            order.order_details
        )

        created_order.order_details = created_details

        event = OrderCreatedEvent(
            payload=created_order.to_dict()
        )

        await self.event_publisher.publish(event)

        return created_order
