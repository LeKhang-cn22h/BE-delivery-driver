#application/services/appove_service.py
from datetime import datetime
from typing import List, Dict
from collections import defaultdict

from domain.models import (
    OrderDetail,
    OrderProcessingResult,
    BatchProcessingResult
)
from domain.Repositories import (
    IOrderRepository,
    IScheduleRepository,
    IScheduleItemRepository
)


class OrderProcessingService:
    """Service xử lý đơn hàng và phân vùng"""

    def __init__(
            self,
            order_repo: IOrderRepository,
            schedule_repo: IScheduleRepository,
            schedule_item_repo: IScheduleItemRepository
    ):
        self.order_repo = order_repo
        self.schedule_repo = schedule_repo
        self.schedule_item_repo = schedule_item_repo

    def _group_orders_by_area(
            self,
            orders: List[OrderDetail]
    ) -> Dict[str, List[OrderDetail]]:
        """
        Nhóm các đơn hàng theo area_code

        Returns:
            Dict với key là area_code, value là list OrderDetail
        """
        grouped = defaultdict(list)
        for order in orders:
            grouped[order.area_code].append(order)
        return dict(grouped)

    def _sort_orders_by_priority(
            self,
            orders: List[OrderDetail]
    ) -> List[OrderDetail]:
        """
        Sắp xếp đơn hàng theo priority_score (ưu tiên cao đến thấp)
        """
        return sorted(orders, key=lambda x: x.priority_score, reverse=True)

    async def _create_schedule_for_area(
            self,
            area_code: str,
            orders: List[OrderDetail],
            post_office_id: str,
            scheduled_date: datetime
    ) -> OrderProcessingResult:
        """
        Tạo schedule cho một vùng cụ thể

        Args:
            area_code: Mã vùng (ward/district/province)
            orders: Danh sách đơn hàng trong vùng
            post_office_id: ID bưu cục
            scheduled_date: Ngày dự kiến giao

        Returns:
            OrderProcessingResult chứa thông tin schedule đã tạo
        """
        # Kiểm tra xem đã có schedule cho ngày và vùng này chưa
        existing_schedule = await self.schedule_repo.get_schedules_by_date_and_area(
            post_office_id=post_office_id,
            scheduled_date=scheduled_date,
            area_code=area_code
        )

        if existing_schedule:
            schedule = existing_schedule
        else:
            # Tạo schedule mới
            schedule_data = {
                "scheduled_date": scheduled_date,
                "area_code": area_code,
                "status": "pending",
                "total_orders": len(orders),
                "completed_orders": 0,
                "failed_orders": 0,
                "post_office_id": post_office_id
            }
            schedule = await self.schedule_repo.create_schedule(schedule_data)

        # Sắp xếp đơn hàng theo độ ưu tiên
        sorted_orders = self._sort_orders_by_priority(orders)

        # Lấy queue number hiện tại lớn nhất
        max_queue = await self.schedule_item_repo.get_max_queue_number(schedule.id)

        # Tạo schedule items cho các đơn hàng
        schedule_items_data = []
        for idx, order in enumerate(sorted_orders, start=max_queue + 1):
            schedule_items_data.append({
                "schedule_id": schedule.id,
                "order_detail_id": order.id,
                "status": "pending",
                "queue": idx
            })

        # Tạo batch schedule items
        await self.schedule_item_repo.create_schedule_items_batch(schedule_items_data)

        # Cập nhật status của order_details sang "scheduled"
        for order in sorted_orders:
            await self.order_repo.update_order_detail_status(
                order_detail_id=order.id,
                status="scheduled"
            )

        # Cập nhật tổng số orders trong schedule nếu có thêm
        if existing_schedule:
            await self.schedule_repo.update_schedule(
                schedule_id=schedule.id,
                update_data={
                    "total_orders": schedule.total_orders + len(orders)
                }
            )

        return OrderProcessingResult(
            schedule_id=schedule.id,
            area_code=area_code,
            total_orders=len(orders),
            order_detail_ids=[order.id for order in sorted_orders],
            created_at=schedule.created_at
        )

    async def process_pending_orders(
            self,
            post_office_id: str,
            scheduled_date: datetime
    ) -> BatchProcessingResult:
        """
        Xử lý tất cả đơn hàng pending của một bưu cục

        Args:
            post_office_id: ID bưu cục
            scheduled_date: Ngày dự kiến giao hàng

        Returns:
            BatchProcessingResult chứa thông tin tất cả schedules đã tạo
        """
        # Lấy tất cả order details có status = pending
        pending_orders = await self.order_repo.get_pending_order_details(
            post_office_id=post_office_id
        )

        if not pending_orders:
            return BatchProcessingResult(
                total_schedules=0,
                total_orders=0,
                schedules=[],
                processed_at=datetime.now()
            )

        # Nhóm đơn hàng theo vùng
        grouped_orders = self._group_orders_by_area(pending_orders)

        # Tạo schedule cho từng vùng
        results = []
        for area_code, orders in grouped_orders.items():
            result = await self._create_schedule_for_area(
                area_code=area_code,
                orders=orders,
                post_office_id=post_office_id,
                scheduled_date=scheduled_date
            )
            results.append(result)

        return BatchProcessingResult(
            total_schedules=len(results),
            total_orders=len(pending_orders),
            schedules=results,
            processed_at=datetime.now()
        )

    async def process_orders_by_area(
            self,
            post_office_id: str,
            area_code: str,
            scheduled_date: datetime
    ) -> OrderProcessingResult:
        """
        Xử lý đơn hàng của một vùng cụ thể

        Args:
            post_office_id: ID bưu cục
            area_code: Mã vùng cần xử lý
            scheduled_date: Ngày dự kiến giao hàng

        Returns:
            OrderProcessingResult cho vùng đó
        """
        # Lấy đơn hàng theo vùng
        orders = await self.order_repo.get_order_details_by_area(
            post_office_id=post_office_id,
            area_code=area_code
        )

        if not orders:
            raise ValueError(f"Không tìm thấy đơn hàng pending cho vùng {area_code}")

        # Tạo schedule cho vùng
        result = await self._create_schedule_for_area(
            area_code=area_code,
            orders=orders,
            post_office_id=post_office_id,
            scheduled_date=scheduled_date
        )

        return result