from typing import List
from datetime import datetime
from collections import defaultdict

# Import từ application/dto thay vì domain/models
from application.dto import OrderProcessingResult, BatchProcessingResult
from domain.models import OrderDetail


class OrderProcessingService:
    def __init__(self, order_repo, schedule_repo, schedule_item_repo):
        self.order_repo = order_repo
        self.schedule_repo = schedule_repo
        self.schedule_item_repo = schedule_item_repo

    async def process_pending_orders(
            self,
            post_office_id: str,
            scheduled_date: datetime
    ) -> BatchProcessingResult:
        """Xử lý tất cả đơn hàng pending, nhóm theo vùng"""

        # 1. Lấy tất cả order_details pending
        order_details = await self.order_repo.get_pending_order_details_by_post_office(
            post_office_id
        )

        if not order_details:
            return BatchProcessingResult(
                total_schedules=0,
                total_orders=0,
                schedules=[]
            )

        # 2. Nhóm theo area_code
        grouped = defaultdict(list)
        for od in order_details:
            area = od.area_code if hasattr(od, 'area_code') else None
            if area:
                grouped[area].append(od)

        # 3. Tạo schedule cho từng vùng
        schedules = []
        total_orders = 0

        for area_code, orders in grouped.items():
            result = await self._create_schedule_for_area(
                post_office_id=post_office_id,
                area_code=area_code,
                scheduled_date=scheduled_date,
                order_details=orders
            )
            schedules.append(result)
            total_orders += result.total_orders

        return BatchProcessingResult(
            total_schedules=len(schedules),
            total_orders=total_orders,
            schedules=schedules
        )

    async def process_orders_by_area(
            self,
            post_office_id: str,
            area_code: str,
            scheduled_date: datetime
    ) -> OrderProcessingResult:
        """Xử lý đơn hàng của một vùng cụ thể"""

        # Lấy order_details theo area
        order_details = await self.order_repo.get_pending_order_details_by_area(
            post_office_id, area_code
        )

        if not order_details:
            raise ValueError(f"Không tìm thấy đơn hàng pending cho vùng {area_code}")

        return await self._create_schedule_for_area(
            post_office_id=post_office_id,
            area_code=area_code,
            scheduled_date=scheduled_date,
            order_details=order_details
        )

    async def _create_schedule_for_area(
            self,
            post_office_id: str,
            area_code: str,
            scheduled_date: datetime,
            order_details: List[OrderDetail]
    ) -> OrderProcessingResult:
        """Tạo schedule và schedule_items cho một vùng"""

        # 1. Tạo schedule
        schedule = await self.schedule_repo.create_schedule(
            post_office_id=post_office_id,
            area_code=area_code,
            scheduled_date=scheduled_date,
            total_orders=len(order_details)
        )

        # 2. Tạo schedule_items
        await self.schedule_item_repo.create_schedule_items(
            schedule_id=schedule.id,
            order_details=order_details
        )

        # 3. Cập nhật status order_details
        order_detail_ids = [od.id for od in order_details]
        await self.order_repo.update_order_details_status(
            order_detail_ids=order_detail_ids,
            status='scheduled'
        )

        return OrderProcessingResult(
            schedule_id=schedule.id,
            area_code=area_code,
            total_orders=len(order_details),
            order_detail_ids=order_detail_ids
        )