# presentation/routes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from uuid import UUID
from infrastructure.database import Database
from infrastructure.supabase.driver_workflow_repository_impl import DriverWorkflowRepository
from application.services.driver_workflow_service import DriverWorkflowService
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/driver", tags=["Driver App"])


def get_service():
    try:
        sb = Database.get_client()
        repo = DriverWorkflowRepository(sb)
        return DriverWorkflowService(repo)
    except Exception as e:
        logger.error(f"Failed to initialize service: {str(e)}", exc_info=True)
        raise


# ================= START SCHEDULE =================
@router.post("/{driver_id}/schedules/{schedule_id}/start")
async def start_schedule(
        driver_id: UUID,
        schedule_id: UUID,
        service: DriverWorkflowService = Depends(get_service)
):
    """
    Driver starts their assigned schedule

    - Updates schedule status to 'in_progress'
    - Updates driver status to 'busy'
    - Initializes driver location tracking
    """
    try:
        logger.info(f"Driver {driver_id} starting schedule {schedule_id}")
        result = await service.start_schedule(driver_id, schedule_id)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Schedule started successfully",
                "data": result
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e),
                "error_type": "ValidationError"
            }
        )
    except Exception as e:
        logger.error(f"Error in start_schedule: {str(e)}")
        logger.error(traceback.format_exc())

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


# presentation/routes.py

@router.post("/{driver_id}/schedules/{schedule_id}/end")
async def end_schedule(
        driver_id: UUID,
        schedule_id: UUID,
        service: DriverWorkflowService = Depends(get_service)
):
    """
    Driver ends their schedule

    - Completes the schedule if all orders are done
    - Sets driver status to 'available'
    - Clears current location tracking
    """
    try:
        logger.info(f"Driver {driver_id} ending schedule {schedule_id}")
        result = await service.end_schedule(driver_id, schedule_id)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Schedule ended successfully",
                "data": result
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e),
                "error_type": "ValidationError"
            }
        )
    except Exception as e:
        logger.error(f"Error in end_schedule: {str(e)}")
        logger.error(traceback.format_exc())

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


@router.post("/{driver_id}/off-duty")
async def set_off_duty(
        driver_id: UUID,
        service: DriverWorkflowService = Depends(get_service)
):
    """
    Driver goes off duty (休息/下班)

    - Sets driver status to 'off_duty'
    - Driver must not have active schedule
    """
    try:
        logger.info(f"Driver {driver_id} going off duty")
        result = await service.set_driver_status(driver_id, "off_duty")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Driver is now off duty",
                "data": result
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error setting off duty: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@router.post("/{driver_id}/on-duty")
async def set_on_duty(
        driver_id: UUID,
        service: DriverWorkflowService = Depends(get_service)
):
    """
    Driver goes on duty (上班)

    - Sets driver status to 'available'
    - Ready to accept schedules
    """
    try:
        logger.info(f"Driver {driver_id} going on duty")
        result = await service.set_driver_status(driver_id, "available")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Driver is now available",
                "data": result
            }
        )
    except Exception as e:
        logger.error(f"Error setting on duty: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )
# ================= TAKE ORDER =================
@router.post("/{driver_id}/orders/{order_detail_id}/take")
async def take_order(
        driver_id: UUID,
        order_detail_id: UUID,
        service: DriverWorkflowService = Depends(get_service)
):
    """
    Driver takes an order from their schedule

    - Verifies order is in driver's schedule
    - Updates order status to 'picking'
    - Updates driver's current order
    """
    try:
        logger.info(f"Driver {driver_id} taking order {order_detail_id}")
        result = await service.take_order(driver_id, order_detail_id)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Order taken successfully",
                "data": result
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e),
                "error_type": "ValidationError"
            }
        )
    except Exception as e:
        logger.error(f"Error in take_order: {str(e)}")
        logger.error(traceback.format_exc())

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


# ================= MARK PICKED UP =================
@router.post("/{driver_id}/orders/{order_detail_id}/picked-up")
async def picked_up(
        driver_id: UUID,
        order_detail_id: UUID,
        service: DriverWorkflowService = Depends(get_service)
):
    """
    Driver marks order as picked up

    - Updates order status to 'picked_up'
    - Updates parent order to 'processing'
    - Changes driver status to 'delivering'
    """
    try:
        logger.info(f"Driver {driver_id} marking order {order_detail_id} as picked up")
        result = await service.mark_picked_up(driver_id, order_detail_id)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Order marked as picked up",
                "data": result
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e),
                "error_type": "ValidationError"
            }
        )
    except Exception as e:
        logger.error(f"Error in picked_up: {str(e)}")
        logger.error(traceback.format_exc())

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


# ================= MARK DELIVERED =================
@router.post("/{driver_id}/orders/{order_detail_id}/delivered")
async def delivered(
        driver_id: UUID,
        order_detail_id: UUID,
        service: DriverWorkflowService = Depends(get_service)
):
    """
    Driver marks order as delivered

    - Updates order status to 'completed'
    - Records delivery timestamp
    - Resets driver to 'idle'
    - Checks if schedule is completed
    """
    try:
        logger.info(f"Driver {driver_id} marking order {order_detail_id} as delivered")
        result = await service.mark_delivered(driver_id, order_detail_id)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Order delivered successfully",
                "data": result
            }
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e),
                "error_type": "ValidationError"
            }
        )
    except Exception as e:
        logger.error(f"Error in delivered: {str(e)}")
        logger.error(traceback.format_exc())

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


# ================= UPDATE LOCATION =================
@router.post("/{driver_id}/location")
async def update_location(
        driver_id: UUID,
        lat: float,
        lng: float,
        speed: float = 0.0,
        heading: float = 0.0,
        service: DriverWorkflowService = Depends(get_service)
):
    """
    Update driver's real-time location

    - Saves to location history
    - Updates current location
    - Tracks with schedule and current order
    """
    try:
        logger.info(f"Updating location for driver {driver_id}: ({lat}, {lng})")
        result = await service.update_location(driver_id, lat, lng, speed, heading)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Location updated",
                "data": result
            }
        )
    except Exception as e:
        logger.error(f"Error in update_location: {str(e)}")
        logger.error(traceback.format_exc())

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


# ================= GET SCHEDULE =================
@router.get("/{driver_id}/schedules/{schedule_id}")
async def get_schedule(
        driver_id: UUID,
        schedule_id: UUID,
        service: DriverWorkflowService = Depends(get_service)
):
    """Get driver's schedule details"""
    try:
        result = await service.get_driver_schedule(driver_id, schedule_id)

        if not result:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "Schedule not found or does not belong to driver"
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result
            }
        )
    except Exception as e:
        logger.error(f"Error getting schedule: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )