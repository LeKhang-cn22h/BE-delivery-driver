"""
Schedule Domain Service - Business Logic
"""
from datetime import datetime
from typing import List, Dict, Optional
from uuid import UUID, uuid4

from domain.entities.schedule import Schedule, ScheduleItem
from domain.entities.driver import Driver
from domain.entities.order import OrderDetail
from domain.services.genetic_scheduler import GeneticScheduler
from infrastructure.config.settings import get_settings


class ScheduleService:
    """Domain service for schedule operations"""

    def __init__(self):
        self.settings = get_settings()
        self.ga_scheduler = GeneticScheduler()

    def create_optimized_schedules(
            self,
            drivers: List[Driver],
            orders: List[OrderDetail],
            scheduled_date: datetime,
            post_office_id: Optional[UUID] = None
    ) -> List[Schedule]:
        """
        Create optimized schedules using Genetic Algorithm

        Args:
            drivers: Available drivers
            orders: Orders to be scheduled
            scheduled_date: Date for scheduling
            post_office_id: Post office ID

        Returns:
            List of Schedule objects with optimized assignments
        """
        # Run GA optimization
        optimized_assignments = self.ga_scheduler.optimize(drivers, orders)

        # Create Schedule objects
        schedules = []
        order_dict = {order.id: order for order in orders}

        for driver in drivers:
            assigned_order_ids = optimized_assignments.get(driver.id, [])

            if not assigned_order_ids:
                continue

            # Determine area code (most common area in assigned orders)
            area_codes = [
                order_dict[oid].area_code
                for oid in assigned_order_ids
                if oid in order_dict and order_dict[oid].area_code
            ]
            primary_area = max(set(area_codes), key=area_codes.count) if area_codes else None

            # Create schedule
            schedule = Schedule(
                id=uuid4(),
                driver_id=driver.id,
                area_code=primary_area,
                scheduled_date=scheduled_date,
                status="pending",
                total_orders=len(assigned_order_ids),
                completed_orders=0,
                failed_orders=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                post_office_id=post_office_id
            )

            # Create schedule items
            for queue_position, order_id in enumerate(assigned_order_ids):
                item = ScheduleItem(
                    id=uuid4(),
                    schedule_id=schedule.id,
                    order_detail_id=order_id,
                    status="pending",
                    queue=queue_position + 1
                )
                schedule.add_item(item)

            schedules.append(schedule)

        return schedules

    def validate_schedule_capacity(
            self,
            driver: Driver,
            new_orders_count: int
    ) -> bool:
        """Validate if driver can handle additional orders"""
        max_orders = self.settings.MAX_ORDERS_PER_DRIVER
        total_orders = driver.current_orders + new_orders_count
        return total_orders <= max_orders

    def calculate_schedule_metrics(
            self,
            schedule: Schedule,
            orders: List[OrderDetail]
    ) -> Dict:
        """Calculate metrics for a schedule"""
        order_dict = {o.id: o for o in orders}

        # Calculate priority distribution
        priorities = []
        for item in schedule.items:
            order = order_dict.get(item.order_detail_id)
            if order:
                priorities.append(order.get_priority())

        avg_priority = sum(priorities) / len(priorities) if priorities else 0

        # Calculate area coverage
        areas = set()
        for item in schedule.items:
            order = order_dict.get(item.order_detail_id)
            if order and order.area_code:
                areas.add(order.area_code)

        metrics = {
            "total_orders": schedule.total_orders,
            "average_priority": round(avg_priority, 2),
            "area_coverage": len(areas),
            "completion_rate": schedule.get_completion_rate(),
            "status": schedule.status
        }

        return metrics

    def reoptimize_schedule(
            self,
            existing_schedule: Schedule,
            new_orders: List[OrderDetail],
            driver: Driver
    ) -> Schedule:
        """
        Re-optimize existing schedule with new orders

        This is useful when adding orders to an existing schedule
        """
        # Combine existing and new orders
        all_order_ids = [item.order_detail_id for item in existing_schedule.items]
        all_order_ids.extend([order.id for order in new_orders])

        # For single driver, just append orders (simple strategy)
        # Could use GA here too for better optimization

        for order in new_orders:
            queue_position = existing_schedule.total_orders + 1
            item = ScheduleItem(
                id=uuid4(),
                schedule_id=existing_schedule.id,
                order_detail_id=order.id,
                status="pending",
                queue=queue_position
            )
            existing_schedule.add_item(item)

        existing_schedule.updated_at = datetime.now()

        return existing_schedule

    def get_schedule_summary(self, schedules: List[Schedule]) -> Dict:
        """Get summary statistics for multiple schedules"""
        if not schedules:
            return {
                "total_schedules": 0,
                "total_drivers": 0,
                "total_orders": 0,
                "avg_orders_per_driver": 0,
                "areas_covered": 0
            }

        total_orders = sum(s.total_orders for s in schedules)
        areas = set(s.area_code for s in schedules if s.area_code)

        return {
            "total_schedules": len(schedules),
            "total_drivers": len(schedules),
            "total_orders": total_orders,
            "avg_orders_per_driver": round(total_orders / len(schedules), 2),
            "areas_covered": len(areas)
        }