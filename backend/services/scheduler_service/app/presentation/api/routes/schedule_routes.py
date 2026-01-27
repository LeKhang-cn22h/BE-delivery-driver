"""
Schedule API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from presentation.api.schemas.schedule_schema import (
    CreateScheduleAPIRequest,
    UpdateScheduleAPIRequest,
    ScheduleResponse,
    ScheduleItemResponse,
    BatchScheduleAPIResponse,
    ScheduleDetailResponse,
    ErrorResponse
)
from presentation.dependencies import (
    get_create_schedule_use_case,
    get_driver_schedule_use_case,
    get_update_schedule_use_case
)
from application.use_cases.create_schedule import CreateScheduleUseCase
from application.use_cases.get_driver_schedule import GetDriverScheduleUseCase
from application.use_cases.update_schedule import UpdateScheduleUseCase
from application.dto.schedule_dto import CreateScheduleRequest, UpdateScheduleRequest

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post(
    "/create",
    response_model=BatchScheduleAPIResponse,
    summary="Create optimized schedules using Genetic Algorithm"
)
async def create_schedules(
        request: CreateScheduleAPIRequest,
        use_case: CreateScheduleUseCase = Depends(get_create_schedule_use_case)
):
    """
    Create optimized schedules for drivers and orders.

    This endpoint uses a Genetic Algorithm to optimize:
    - Order priority satisfaction
    - Distance/area clustering
    - Load balancing among drivers

    **Process:**
    1. Fetch available drivers
    2. Fetch pending orders
    3. Run GA optimization (200 generations by default)
    4. Create schedules in database
    5. Update order statuses to 'scheduled'

    **Parameters:**
    - **scheduled_date**: Target date for delivery (YYYY-MM-DD)
    - **post_office_id**: Filter by post office (optional)
    - **area_code**: Filter orders by area (optional)
    - **driver_ids**: Use specific drivers (optional)
    - **order_limit**: Max orders to schedule (optional)
    - **use_genetic_algorithm**: Enable GA optimization (default: true)
    """
    try:
        # Convert API request to DTO
        dto_request = CreateScheduleRequest(
            scheduled_date=datetime.fromisoformat(request.scheduled_date),
            post_office_id=UUID(request.post_office_id) if request.post_office_id else None,
            area_code=request.area_code,
            driver_ids=[UUID(d) for d in request.driver_ids] if request.driver_ids else None,
            order_limit=request.order_limit,
            use_genetic_algorithm=request.use_genetic_algorithm
        )

        # Execute use case
        result = await use_case.execute(dto_request)

        # Convert to API response
        schedules_response = [
            ScheduleResponse(
                id=str(s.id),
                driver_id=str(s.driver_id),
                area_code=s.area_code,
                scheduled_date=s.scheduled_date,
                status=s.status,
                total_orders=s.total_orders,
                completed_orders=s.completed_orders,
                failed_orders=s.failed_orders,
                created_at=s.created_at,
                updated_at=s.updated_at,
                post_office_id=str(s.post_office_id) if s.post_office_id else None,
                items=[
                    ScheduleItemResponse(
                        id=str(item.id),
                        schedule_id=str(item.schedule_id),
                        order_detail_id=str(item.order_detail_id),
                        status=item.status,
                        delivered_at=item.delivered_at,
                        failure_reason=item.failure_reason,
                        queue=item.queue
                    )
                    for item in s.items
                ]
            )
            for s in result.schedules
        ]

        return BatchScheduleAPIResponse(
            success=True,
            message=f"Successfully created {len(schedules_response)} schedules",
            schedules=schedules_response,
            summary=result.summary,
            optimization_time=result.optimization_time
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/driver/{driver_id}",
    response_model=List[ScheduleResponse],
    summary="Get schedules for a specific driver"
)
async def get_driver_schedules(
        driver_id: str,
        start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
        use_case: GetDriverScheduleUseCase = Depends(get_driver_schedule_use_case)
):
    """
    Retrieve all schedules assigned to a specific driver.

    **Optional filters:**
    - **start_date**: Filter schedules from this date
    - **end_date**: Filter schedules until this date
    """
    try:
        driver_uuid = UUID(driver_id)
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        schedules = await use_case.execute(
            driver_id=driver_uuid,
            start_date=start_dt,
            end_date=end_dt
        )

        # Convert to API response
        return [
            ScheduleResponse(
                id=str(s.id),
                driver_id=str(s.driver_id),
                area_code=s.area_code,
                scheduled_date=s.scheduled_date,
                status=s.status,
                total_orders=s.total_orders,
                completed_orders=s.completed_orders,
                failed_orders=s.failed_orders,
                created_at=s.created_at,
                updated_at=s.updated_at,
                post_office_id=str(s.post_office_id) if s.post_office_id else None,
                items=[
                    ScheduleItemResponse(
                        id=str(item.id),
                        schedule_id=str(item.schedule_id),
                        order_detail_id=str(item.order_detail_id),
                        status=item.status,
                        delivered_at=item.delivered_at,
                        failure_reason=item.failure_reason,
                        queue=item.queue
                    )
                    for item in s.items
                ]
            )
            for s in schedules
        ]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put(
    "/{schedule_id}",
    response_model=ScheduleDetailResponse,
    summary="Update an existing schedule"
)
async def update_schedule(
        schedule_id: str,
        request: UpdateScheduleAPIRequest,
        use_case: UpdateScheduleUseCase = Depends(get_update_schedule_use_case)
):
    """
    Update schedule details.

    **Supported operations:**
    - Change schedule status
    - Add new orders to schedule
    - Remove orders from schedule
    """
    try:
        schedule_uuid = UUID(schedule_id)

        # Convert API request to DTO
        dto_request = UpdateScheduleRequest(
            status=request.status,
            add_order_ids=[UUID(oid) for oid in request.add_order_ids] if request.add_order_ids else None,
            remove_order_ids=[UUID(oid) for oid in request.remove_order_ids] if request.remove_order_ids else None
        )

        result = await use_case.execute(schedule_uuid, dto_request)

        # Convert to API response
        schedule_response = ScheduleResponse(
            id=str(result.schedule.id),
            driver_id=str(result.schedule.driver_id),
            area_code=result.schedule.area_code,
            scheduled_date=result.schedule.scheduled_date,
            status=result.schedule.status,
            total_orders=result.schedule.total_orders,
            completed_orders=result.schedule.completed_orders,
            failed_orders=result.schedule.failed_orders,
            created_at=result.schedule.created_at,
            updated_at=result.schedule.updated_at,
            post_office_id=str(result.schedule.post_office_id) if result.schedule.post_office_id else None,
            items=[
                ScheduleItemResponse(
                    id=str(item.id),
                    schedule_id=str(item.schedule_id),
                    order_detail_id=str(item.order_detail_id),
                    status=item.status,
                    delivered_at=item.delivered_at,
                    failure_reason=item.failure_reason,
                    queue=item.queue
                )
                for item in result.schedule.items
            ]
        )

        return ScheduleDetailResponse(
            success=True,
            schedule=schedule_response,
            metrics=result.metrics
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/{schedule_id}",
    summary="Delete a schedule"
)
async def delete_schedule(
        schedule_id: str,
        schedule_repo=Depends(get_create_schedule_use_case)
):
    """
    Delete a schedule and reset associated orders to pending status.
    """
    try:
        schedule_uuid = UUID(schedule_id)

        # Get schedule repository from use case
        from app.presentation.dependencies import get_schedule_repository, get_order_repository
        schedule_repo = get_schedule_repository()
        order_repo = get_order_repository()

        # Get schedule
        schedule = await schedule_repo.get_schedule_by_id(schedule_uuid)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Reset orders to pending
        for item in schedule.items:
            await order_repo.update_order_status(item.order_detail_id, "pending")

        # Delete schedule
        deleted = await schedule_repo.delete_schedule(schedule_uuid)

        if not deleted:
            raise HTTPException(status_code=404, detail="Schedule not found")

        return {
            "success": True,
            "message": "Schedule deleted successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")