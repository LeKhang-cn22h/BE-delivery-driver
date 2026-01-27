"""
API Request/Response Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID


class CreateScheduleAPIRequest(BaseModel):
    """API request to create schedules"""
    scheduled_date: str = Field(
        ...,
        description="Date for scheduling (YYYY-MM-DD format)",
        example="2025-01-28"
    )
    post_office_id: Optional[str] = Field(
        None,
        description="Post office ID filter"
    )
    area_code: Optional[str] = Field(
        None,
        description="Area code filter",
        example="Q1"
    )
    driver_ids: Optional[List[str]] = Field(
        None,
        description="Specific drivers to use"
    )
    order_limit: Optional[int] = Field(
        None,
        description="Maximum orders to schedule",
        ge=1,
        le=1000
    )
    use_genetic_algorithm: bool = Field(
        True,
        description="Use GA optimization (recommended)"
    )

    @validator('scheduled_date')
    def validate_date(cls, v):
        """Validate date format"""
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")


class UpdateScheduleAPIRequest(BaseModel):
    """API request to update schedule"""
    status: Optional[str] = Field(
        None,
        description="New status",
        pattern="^(pending|active|completed|cancelled)$"
    )
    add_order_ids: Optional[List[str]] = Field(
        None,
        description="Order IDs to add to schedule"
    )
    remove_order_ids: Optional[List[str]] = Field(
        None,
        description="Order IDs to remove from schedule"
    )


class ScheduleItemResponse(BaseModel):
    """API response for schedule item"""
    id: str
    schedule_id: str
    order_detail_id: str
    status: str
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    queue: Optional[int] = None


class ScheduleResponse(BaseModel):
    """API response for schedule"""
    id: str
    driver_id: str
    area_code: Optional[str] = None
    scheduled_date: datetime
    status: str
    total_orders: int
    completed_orders: int
    failed_orders: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    post_office_id: Optional[str] = None
    items: List[ScheduleItemResponse]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BatchScheduleAPIResponse(BaseModel):
    """API response for batch schedule creation"""
    success: bool
    message: str
    schedules: List[ScheduleResponse]
    summary: dict
    optimization_time: Optional[float] = None


class ScheduleDetailResponse(BaseModel):
    """API response with schedule and metrics"""
    success: bool
    schedule: ScheduleResponse
    metrics: dict


class ErrorResponse(BaseModel):
    """API error response"""
    success: bool = False
    error: str
    details: Optional[dict] = None


class GetSchedulesQuery(BaseModel):
    """Query parameters for getting schedules"""
    start_date: Optional[str] = Field(
        None,
        description="Start date (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None,
        description="End date (YYYY-MM-DD)"
    )
    status: Optional[str] = Field(
        None,
        description="Filter by status"
    )

    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        """Validate date format"""
        if v:
            try:
                datetime.fromisoformat(v)
                return v
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v