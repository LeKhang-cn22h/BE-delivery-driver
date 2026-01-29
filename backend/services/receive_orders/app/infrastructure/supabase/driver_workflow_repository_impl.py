# infrastructure/supabase/driver_workflow_repository_impl.py
from domain.repositories.driver_workflow_repository import IDriverWorkflowRepository
from uuid import UUID
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DriverWorkflowRepository(IDriverWorkflowRepository):

    def __init__(self, supabase):
        self.sb = supabase  # Already schema("delivery")

    def get_driver_schedule(self, driver_id: UUID, schedule_id: UUID) -> Optional[dict]:
        """Get and verify driver's schedule"""
        result = (
            self.sb.table("schedules")
            .select("*")
            .eq("id", str(schedule_id))
            .eq("driver_id", str(driver_id))
            .execute()
        )

        if not result.data or len(result.data) == 0:
            return None

        return result.data[0]

    def start_schedule(self, driver_id: UUID, schedule_id: UUID) -> dict:
        """
        Driver starts their schedule:
        1. Verify schedule belongs to driver
        2. Update schedule status to 'in_progress'
        3. Update driver status to 'busy'
        4. Initialize or update driver_current_locations
        """
        logger.info(f"Driver {driver_id} starting schedule {schedule_id}")

        # Verify schedule belongs to driver
        schedule = self.get_driver_schedule(driver_id, schedule_id)
        if not schedule:
            raise ValueError(
                f"Schedule {schedule_id} not found or does not belong to driver {driver_id}"
            )

        # Check if schedule is in valid state to start
        if schedule['status'] not in ['draft', 'confirmed']:
            raise ValueError(
                f"Cannot start schedule with status '{schedule['status']}'. "
                f"Schedule must be in 'draft' or 'confirmed' status."
            )

        # Update schedule status
        self.sb.table("schedules").update({
            "status": "in_progress"
        }).eq("id", str(schedule_id)).execute()

        # Update driver status
        self.sb.table("drivers").update({
            "status": "busy"
        }).eq("id", str(driver_id)).execute()

        # Check if driver_current_locations exists
        existing_location = (
            self.sb.table("driver_current_locations")
            .select("*")
            .eq("driver_id", str(driver_id))
            .execute()
        )

        if existing_location.data and len(existing_location.data) > 0:
            # Update existing location
            self.sb.table("driver_current_locations").update({
                "schedule_id": str(schedule_id),
                "status": "idle",
                "current_order_detail_id": None,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("driver_id", str(driver_id)).execute()
        else:
            # Insert new location record with default position
            self.sb.table("driver_current_locations").insert({
                "driver_id": str(driver_id),
                "schedule_id": str(schedule_id),
                "status": "idle",
                "location": "POINT(0 0)",  # Default location
                "speed": 0.0,
                "heading": 0.0
            }).execute()

        logger.info(f"Schedule {schedule_id} started successfully by driver {driver_id}")

        return {
            "schedule_id": str(schedule_id),
            "driver_id": str(driver_id),
            "status": "in_progress"
        }

    # infrastructure/supabase/driver_workflow_repository_impl.py

    def end_schedule(self, driver_id: UUID, schedule_id: UUID) -> dict:
        """
        Driver ends their schedule:
        1. Verify schedule belongs to driver
        2. Check if all orders are completed
        3. Update schedule status to 'completed'
        4. Set driver status to 'available'
        5. Clear driver_current_locations
        """
        logger.info(f"Driver {driver_id} ending schedule {schedule_id}")

        # Verify schedule belongs to driver
        schedule = self.get_driver_schedule(driver_id, schedule_id)
        if not schedule:
            raise ValueError(
                f"Schedule {schedule_id} not found or does not belong to driver {driver_id}"
            )

        # Check schedule status
        if schedule['status'] != 'in_progress':
            raise ValueError(
                f"Cannot end schedule with status '{schedule['status']}'. "
                f"Schedule must be 'in_progress'."
            )

        # Count schedule items
        schedule_items = (
            self.sb.table("schedule_items")
            .select("status")
            .eq("schedule_id", str(schedule_id))
            .execute()
        )

        if schedule_items.data:
            total = len(schedule_items.data)
            completed = sum(1 for item in schedule_items.data
                            if item.get("status") == "delivered")
            failed = sum(1 for item in schedule_items.data
                         if item.get("status") == "failed")
            pending = total - completed - failed

            # Update schedule
            self.sb.table("schedules").update({
                "status": "completed",
                "total_orders": total,
                "completed_orders": completed,
                "failed_orders": failed
            }).eq("id", str(schedule_id)).execute()

            logger.info(f"Schedule completed: {completed}/{total} delivered, {failed} failed, {pending} pending")
        else:
            # No items, just mark as completed
            self.sb.table("schedules").update({
                "status": "completed"
            }).eq("id", str(schedule_id)).execute()

        # Set driver to available
        self.sb.table("drivers").update({
            "status": "available"
        }).eq("id", str(driver_id)).execute()

        # Clear current location
        self.sb.table("driver_current_locations").delete().eq(
            "driver_id", str(driver_id)
        ).execute()

        logger.info(f"Schedule {schedule_id} ended by driver {driver_id}")

        return {
            "schedule_id": str(schedule_id),
            "driver_id": str(driver_id),
            "status": "completed"
        }

    def set_driver_status(self, driver_id: UUID, status: str) -> dict:
        """
        Update driver status

        Valid statuses: 'available', 'busy', 'off_duty', 'inactive'
        """
        logger.info(f"Setting driver {driver_id} status to {status}")

        # Validate status
        valid_statuses = ['available', 'busy', 'off_duty', 'inactive']
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
            )

        # Check if driver has active schedule
        if status in ['off_duty', 'inactive']:
            current_location = (
                self.sb.table("driver_current_locations")
                .select("schedule_id")
                .eq("driver_id", str(driver_id))
                .execute()
            )

            if current_location.data and len(current_location.data) > 0:
                schedule_id = current_location.data[0].get("schedule_id")
                if schedule_id:
                    # Check schedule status
                    schedule = (
                        self.sb.table("schedules")
                        .select("status")
                        .eq("id", schedule_id)
                        .execute()
                    )

                    if schedule.data and schedule.data[0].get("status") == "in_progress":
                        raise ValueError(
                            f"Cannot set status to '{status}'. "
                            f"Driver has an active schedule {schedule_id}. "
                            f"Please end the schedule first."
                        )

        # Update driver status
        self.sb.table("drivers").update({
            "status": status
        }).eq("id", str(driver_id)).execute()

        logger.info(f"Driver {driver_id} status updated to {status}")

        return {
            "driver_id": str(driver_id),
            "status": status
        }
    def take_order(self, driver_id: UUID, order_detail_id: UUID) -> dict:
        """
        Driver takes an order from schedule:
        1. Verify order is in driver's current schedule
        2. Update order_detail status to 'picking'
        3. Update driver_current_locations with current order
        """
        logger.info(f"Driver {driver_id} taking order {order_detail_id}")

        # Get driver's current schedule
        current_location = (
            self.sb.table("driver_current_locations")
            .select("schedule_id")
            .eq("driver_id", str(driver_id))
            .execute()
        )

        if not current_location.data or len(current_location.data) == 0:
            raise ValueError(f"Driver {driver_id} has no active schedule")

        schedule_id = current_location.data[0].get("schedule_id")
        if not schedule_id:
            raise ValueError(f"Driver {driver_id} has no active schedule")

        # Verify order is in the schedule
        schedule_item = (
            self.sb.table("schedule_items")
            .select("*")
            .eq("schedule_id", schedule_id)
            .eq("order_detail_id", str(order_detail_id))
            .execute()
        )

        if not schedule_item.data or len(schedule_item.data) == 0:
            raise ValueError(
                f"Order {order_detail_id} is not in driver's schedule {schedule_id}"
            )

        # Update order_detail status
        self.sb.table("order_details").update({
            "status": "picking"
        }).eq("id", str(order_detail_id)).execute()

        # Update driver location
        self.sb.table("driver_current_locations").update({
            "current_order_detail_id": str(order_detail_id),
            "status": "moving",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("driver_id", str(driver_id)).execute()

        logger.info(f"Order {order_detail_id} taken by driver {driver_id}")

        return {
            "order_detail_id": str(order_detail_id),
            "driver_id": str(driver_id),
            "status": "picking"
        }

    def mark_picked_up(self, driver_id: UUID, order_detail_id: UUID) -> dict:
        """
        Driver marks order as picked up:
        1. Update order_detail status to 'picked_up'
        2. Update parent order status to 'processing'
        3. Update driver status to 'delivering'
        """
        logger.info(f"Driver {driver_id} marking order {order_detail_id} as picked up")

        # Get order_detail to find parent order
        order_detail = (
            self.sb.table("order_details")
            .select("order_id, status")
            .eq("id", str(order_detail_id))
            .execute()
        )

        if not order_detail.data or len(order_detail.data) == 0:
            raise ValueError(f"Order detail {order_detail_id} not found")

        order_id = order_detail.data[0].get("order_id")
        current_status = order_detail.data[0].get("status")

        # Verify current status
        if current_status != "picking":
            raise ValueError(
                f"Cannot mark as picked up. Order is in '{current_status}' status, "
                f"expected 'picking'"
            )

        # Update order_detail
        self.sb.table("order_details").update({
            "status": "picked_up"
        }).eq("id", str(order_detail_id)).execute()

        # Update parent order
        if order_id:
            self.sb.table("orders").update({
                "status": "processing"
            }).eq("id", order_id).execute()

        # Update driver location status
        self.sb.table("driver_current_locations").update({
            "status": "delivering",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("driver_id", str(driver_id)).execute()

        logger.info(f"Order {order_detail_id} marked as picked up by driver {driver_id}")

        return {
            "order_detail_id": str(order_detail_id),
            "driver_id": str(driver_id),
            "status": "picked_up"
        }

    def mark_delivered(self, driver_id: UUID, order_detail_id: UUID) -> dict:
        """
        Driver marks order as delivered:
        1. Update order_detail status to 'completed'
        2. Update schedule_items with delivered_at
        3. Reset driver to idle status
        4. Check if all orders in schedule are completed
        """
        logger.info(f"Driver {driver_id} marking order {order_detail_id} as delivered")

        # Get order_detail
        order_detail = (
            self.sb.table("order_details")
            .select("status")
            .eq("id", str(order_detail_id))
            .execute()
        )

        if not order_detail.data or len(order_detail.data) == 0:
            raise ValueError(f"Order detail {order_detail_id} not found")

        current_status = order_detail.data[0].get("status")

        # Verify current status
        if current_status != "picked_up":
            raise ValueError(
                f"Cannot mark as delivered. Order is in '{current_status}' status, "
                f"expected 'picked_up'"
            )

        # Update order_detail
        self.sb.table("order_details").update({
            "status": "completed",
            "finish_at": datetime.utcnow().isoformat()
        }).eq("id", str(order_detail_id)).execute()

        # Update schedule_items
        self.sb.table("schedule_items").update({
            "status": "delivered",
            "delivered_at": datetime.utcnow().isoformat()
        }).eq("order_detail_id", str(order_detail_id)).execute()

        # Reset driver location
        self.sb.table("driver_current_locations").update({
            "status": "idle",
            "current_order_detail_id": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("driver_id", str(driver_id)).execute()

        # Get current schedule to check completion
        current_location = (
            self.sb.table("driver_current_locations")
            .select("schedule_id")
            .eq("driver_id", str(driver_id))
            .execute()
        )

        if current_location.data and len(current_location.data) > 0:
            schedule_id = current_location.data[0].get("schedule_id")

            if schedule_id:
                # Count completed vs total orders
                schedule_items = (
                    self.sb.table("schedule_items")
                    .select("status")
                    .eq("schedule_id", schedule_id)
                    .execute()
                )

                if schedule_items.data:
                    total = len(schedule_items.data)
                    completed = sum(1 for item in schedule_items.data
                                    if item.get("status") == "delivered")
                    failed = sum(1 for item in schedule_items.data
                                 if item.get("status") == "failed")

                    # Update schedule counts
                    self.sb.table("schedules").update({
                        "total_orders": total,
                        "completed_orders": completed,
                        "failed_orders": failed
                    }).eq("id", schedule_id).execute()

                    # If all orders are done, mark schedule as completed
                    if completed + failed == total:
                        self.sb.table("schedules").update({
                            "status": "completed"
                        }).eq("id", schedule_id).execute()

                        # Set driver to available
                        self.sb.table("drivers").update({
                            "status": "available"
                        }).eq("id", str(driver_id)).execute()

        logger.info(f"Order {order_detail_id} marked as delivered by driver {driver_id}")

        return {
            "order_detail_id": str(order_detail_id),
            "driver_id": str(driver_id),
            "status": "completed"
        }

    def update_location(
            self,
            driver_id: UUID,
            lat: float,
            lng: float,
            speed: float,
            heading: float
    ) -> dict:
        """
        Update driver's real-time location:
        1. Insert into driver_location_history
        2. Update driver_current_locations
        """
        logger.info(f"Updating location for driver {driver_id}: ({lat}, {lng})")

        # PostGIS format: POINT(longitude latitude)
        point = f"POINT({lng} {lat})"

        # Get current schedule and order
        current = (
            self.sb.table("driver_current_locations")
            .select("schedule_id, current_order_detail_id")
            .eq("driver_id", str(driver_id))
            .execute()
        )

        schedule_id = None
        order_detail_id = None

        if current.data and len(current.data) > 0:
            schedule_id = current.data[0].get("schedule_id")
            order_detail_id = current.data[0].get("current_order_detail_id")

        # Insert into history
        history_data = {
            "driver_id": str(driver_id),
            "location": point,
            "speed": speed,
            "heading": heading
        }

        if schedule_id:
            history_data["schedule_id"] = schedule_id
        if order_detail_id:
            history_data["order_detail_id"] = order_detail_id

        self.sb.table("driver_location_history").insert(history_data).execute()

        # Update current location
        self.sb.table("driver_current_locations").update({
            "location": point,
            "speed": speed,
            "heading": heading,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("driver_id", str(driver_id)).execute()

        logger.info(f"Location updated for driver {driver_id}")

        return {
            "driver_id": str(driver_id),
            "location": {"lat": lat, "lng": lng},
            "speed": speed,
            "heading": heading
        }