from fastapi import APIRouter, HTTPException, Depends, status, Query, Path
from typing import List, Optional
from pydantic import BaseModel
import logging
import os

from application.use_cases.create_order import CreateOrderUseCase
from application.use_cases.get_order import GetOrderUseCase
from application.use_cases.list_customer_orders import ListCustomerOrdersUseCase
from application.use_cases.cancel_order import CancelOrderUseCase
from application.use_cases.update_order_status import UpdateOrderStatusUseCase
from application.dto.order_dto import (
    OrderCreateDTO,
    OrderResponseDTO,
    OrderSummaryDTO,
    OrderDetailResponseDTO,
    PickupStatus
)
from domain.entities.order import OrderDetail, DetailStatus, OrderType, Order
from infrastructure.database.supabase_order_detail_repository import SupabaseOrderDetailRepository
from infrastructure.database.supabase_order_repository import SupabaseOrderRepository
from infrastructure.database.supabase_client import SupabaseClient

# ============= THAY ĐỔI Ở ĐÂY =============
from infrastructure.events.kafka_event_publisher import KafkaEventPublisher

# from infrastructure.events.simple_event_publisher import SimpleEventPublisher  # Comment lại
# ==========================================

logger = logging.getLogger(__name__)

# ============================================================================
# ORDERS ROUTER
# ============================================================================

order_router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

# ============= SINGLETON EVENT PUBLISHER =============
_event_publisher_instance = None


async def get_event_publisher():
    """
    Singleton dependency cho Kafka Event Publisher
    Tự động khởi tạo và start producer lần đầu tiên được gọi
    """
    global _event_publisher_instance

    if _event_publisher_instance is None:
        # Lấy bootstrap servers từ environment variable
        # Trong Docker: kafka:9093
        # Local: localhost:9092
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9093")

        logger.info(f"Initializing Kafka Event Publisher: {bootstrap_servers}")

        _event_publisher_instance = KafkaEventPublisher(bootstrap_servers)
        await _event_publisher_instance.start()

        logger.info("✅ Kafka Event Publisher initialized and started")

    return _event_publisher_instance


# =====================================================

# Dependency injection
def get_order_repository():
    return SupabaseOrderRepository()


def get_order_detail_repository():
    return SupabaseOrderDetailRepository()


def get_create_order_use_case(
        order_repo=Depends(get_order_repository),
        detail_repo=Depends(get_order_detail_repository),
        event_publisher=Depends(get_event_publisher)  # ← Async dependency
):
    return CreateOrderUseCase(order_repo, detail_repo, event_publisher)


def get_get_order_use_case(
        order_repo=Depends(get_order_repository),
        detail_repo=Depends(get_order_detail_repository)
):
    return GetOrderUseCase(order_repo, detail_repo)


def get_list_orders_use_case(
        order_repo=Depends(get_order_repository),
        detail_repo=Depends(get_order_detail_repository)
):
    return ListCustomerOrdersUseCase(order_repo, detail_repo)


def get_cancel_order_use_case(order_repo=Depends(get_order_repository)):
    return CancelOrderUseCase(order_repo)


def get_update_status_use_case(order_repo=Depends(get_order_repository)):
    return UpdateOrderStatusUseCase(order_repo)


@order_router.post("/", response_model=OrderResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_order(
        order_data: OrderCreateDTO,
        use_case: CreateOrderUseCase = Depends(get_create_order_use_case)
):
    """
    Tạo đơn hàng mới

    **Flow khách hàng đặt hàng:**
    1. Khách chọn bưu cục (post_office_id)
    2. Khách nhập địa chỉ lấy hàng (pickup_point, pickup_address, pickup_phone)
    3. Khách nhập danh sách kiện hàng cần giao:
       - Mỗi kiện có: địa chỉ giao, giá cước
       - Có thể giao đến nhiều địa chỉ khác nhau
    4. Hệ thống tạo 1 order + nhiều order_details
    """
    try:
        # Convert DTO to domain
        order_details = [
            OrderDetail(
                id=None,
                order_id=None,
                start_point=detail.start_point,
                address_detail=detail.address_detail,
                area_code=detail.area_code,
                location=detail.location,
                status=DetailStatus.pending,
                priority_score=detail.priority_score,
                note_send=detail.note_send,
                recipient_id=detail.recipient_id

            )
            for detail in order_data.order_details
        ]

        order = Order(
            id=None,
            user_id=order_data.user_id,
            post_office_id=order_data.post_office_id,
            pickup_point=order_data.pickup_point,
            pickup_address=order_data.pickup_address,
            pickup_area_code=order_data.pickup_area_code,
            pickup_location=order_data.pickup_location,
            pickup_phone=order_data.pickup_phone,
            pickup_note=order_data.pickup_note,
            status=None,  # Will be set in use case
            order_type=OrderType(order_data.order_type),
            pickup_status=PickupStatus.pending,
            created_at=None,
            order_details=order_details
        )

        created_order = await use_case.execute(order)

        return OrderResponseDTO(
            id=created_order.id,
            user_id=created_order.user_id,
            post_office_id=created_order.post_office_id,
            pickup_point=created_order.pickup_point,
            pickup_address=created_order.pickup_address,
            pickup_area_code=created_order.pickup_area_code,
            pickup_phone=created_order.pickup_phone,
            pickup_note=created_order.pickup_note,
            status=created_order.status.value,
            order_type=created_order.order_type.value,
            pickup_status=created_order.pickup_status.value,
            created_at=created_order.created_at,
            total_packages=created_order.get_total_packages(),
            delivered_packages=created_order.get_delivered_packages(),
            failed_packages=created_order.get_failed_packages(),
            order_details=[
                OrderDetailResponseDTO(
                    id=d.id,
                    order_id=d.order_id,
                    start_point=d.start_point,
                    address_detail=d.address_detail,
                    area_code=d.area_code,
                    status=d.status.value,
                    priority_score=d.priority_score,
                    note_send=d.note_send,
                    recipient_id=d.recipient_id

                )
                for d in created_order.order_details
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


@order_router.get("/{order_id}", response_model=OrderResponseDTO)
async def get_order(
        order_id: str,
        use_case: GetOrderUseCase = Depends(get_get_order_use_case)
):
    """
    Xem chi tiết đơn hàng

    Trả về đầy đủ thông tin:
    - Thông tin lấy hàng
    - Trạng thái đơn hàng
    - Danh sách tất cả kiện hàng
    - Thống kê: tổng kiện, đã giao, thất bại
    """
    try:
        order = await use_case.execute(order_id)

        return OrderResponseDTO(
            id=order.id,
            user_id=order.user_id,
            post_office_id=order.post_office_id,
            pickup_point=order.pickup_point,
            pickup_address=order.pickup_address,
            pickup_area_code=order.pickup_area_code,
            pickup_phone=order.pickup_phone,
            pickup_note=order.pickup_note,
            status=order.status.value,
            order_type=order.order_type.value,
            created_at=order.created_at,
            total_packages=order.get_total_packages(),
            delivered_packages=order.get_delivered_packages(),
            failed_packages=order.get_failed_packages(),
            order_details=[
                OrderDetailResponseDTO(
                    id=d.id,
                    order_id=d.order_id,
                    start_point=d.start_point,
                    address_detail=d.address_detail,
                    area_code=d.area_code,
                    status=d.status.value,
                    priority_score=d.priority_score,
                    note_send=d.note_send,
                    recipient_id=d.recipient_id

                )
                for d in order.order_details
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@order_router.get("/post-office/{post_office_id}/orders", response_model=List[OrderSummaryDTO])
async def get_post_office_orders(
        post_office_id: str,
        status: Optional[str] = Query(None, regex="^(pending|confirmed|processing|completed|cancelled)$"),
        pickup_status: Optional[str] = Query(None, regex="^(pending|scheduled|picked|failed)$"),
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        use_case: GetOrderUseCase = Depends(get_get_order_use_case)
):
    """
    Lấy danh sách đơn hàng của bưu cục với các filter tùy chọn

    Hỗ trợ các query params:
    - status: Lọc theo trạng thái đơn hàng
    - pickup_status: Lọc theo trạng thái lấy hàng
    - Có thể kết hợp cả 2
    - Nếu không truyền filter nào -> lấy tất cả

    Examples:
    GET /post-office/xxx/orders
    GET /post-office/xxx/orders?status=pending
    GET /post-office/xxx/orders?pickup_status=picked
    GET /post-office/xxx/orders?status=confirmed&pickup_status=pending
    """
    try:
        # Xử lý logic dựa trên params
        if status and pickup_status:
            # Lọc theo cả 2
            orders = await use_case.getbyStatusPickStatus(post_office_id, status, pickup_status)
        elif status:
            # Chỉ lọc theo status
            orders = await use_case.getbyStatus(post_office_id, status)
        elif pickup_status:
            # Chỉ lọc theo pickup_status
            orders = await use_case.getbyPickupStatus(post_office_id, pickup_status)
        else:
            # Không filter, lấy tất cả
            orders = await use_case.getbyPost(post_office_id)

        return [
            OrderSummaryDTO(
                id=order.id,
                pickup_point=order.pickup_point,
                status=order.status,
                created_at=order.created_at,
                pickup_status=order.pickup_status,
                total_packages=order.get_total_packages()
            )
            for order in orders
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@order_router.get("/customer/{user_id}", response_model=List[OrderSummaryDTO])
async def list_customer_orders(
        user_id: str,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        use_case: ListCustomerOrdersUseCase = Depends(get_list_orders_use_case)
):
    """
    Lịch sử đơn hàng của khách hàng

    Trả về danh sách tóm tắt:
    - Địa chỉ lấy hàng
    - Tổng số kiện
    - Tổng phí
    - Trạng thái
    """
    try:
        orders = await use_case.execute(user_id, skip, limit)

        return [
            OrderSummaryDTO(
                id=order.id,
                pickup_point=order.pickup_point,
                status=order.status.value,
                created_at=order.created_at,
                total_packages=order.get_total_packages(),
            )
            for order in orders
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@order_router.post("/{order_id}/cancel")
async def cancel_order(
        order_id: str,
        user_id: str = Query(..., description="ID khách hàng"),
        reason: str = Query(None, description="Lý do hủy"),
        use_case: CancelOrderUseCase = Depends(get_cancel_order_use_case)
):
    """
    Khách hàng hủy đơn hàng

    Chỉ được hủy khi đơn ở trạng thái:
    - PENDING (Chờ xử lý)
    - CONFIRMED (Đã xác nhận)
    """
    try:
        success = await use_case.execute(order_id, user_id, reason)
        return {
            "success": success,
            "message": "Đã hủy đơn hàng thành công"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@order_router.patch("/{order_id}/status")
async def update_order_status(
        order_id: str,
        new_status: str = Query(
            ...,
            regex="^(pending|confirmed|picking_up|picked_up|in_transit|delivering|completed|cancelled)$",
            description="Trạng thái mới"
        ),
        use_case: UpdateOrderStatusUseCase = Depends(get_update_status_use_case)
):
    """
    Cập nhật trạng thái đơn hàng

    Các trạng thái:
    - pending: Chờ xử lý
    - confirmed: Đã xác nhận
    - picking_up: Đang đến lấy hàng
    - picked_up: Đã lấy hàng
    - in_transit: Đang vận chuyển
    - delivering: Đang giao hàng
    - completed: Hoàn thành
    - cancelled: Đã hủy
    """
    try:
        success = await use_case.execute(order_id, new_status)
        return {
            "success": success,
            "message": f"Đã cập nhật trạng thái: {new_status}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# POST OFFICES ROUTER
# ============================================================================

post_office_router = APIRouter(prefix="/api/v1/post-offices", tags=["post-offices"])


class PostOfficeDTO(BaseModel):
    id: str
    code: str
    name: str
    address: str
    district: str
    province: str
    phone: str
    open_time: str
    close_time: str
    status: str


@post_office_router.get("/active", response_model=List[PostOfficeDTO])
async def get_active_post_offices():
    """
    Lấy danh sách bưu cục đang hoạt động
    Dùng cho dropdown khi khách hàng đặt hàng
    """
    client = SupabaseClient.get_client()

    response = (
        client.schema("delivery")
        .table("post_offices")
        .select("id, code, name, address, district, province, phone, open_time, close_time, status")
        .eq("status", "active")
        .order("name")
        .execute()
    )

    return response.data


@post_office_router.get("/{post_office_id}", response_model=PostOfficeDTO)
async def get_post_office(post_office_id: str):
    """Chi tiết một bưu cục"""
    client = SupabaseClient.get_client()

    response = (
        client.schema("delivery")
        .table("post_offices")
        .select("*")
        .eq("id", post_office_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy bưu cục")

    return response.data[0]