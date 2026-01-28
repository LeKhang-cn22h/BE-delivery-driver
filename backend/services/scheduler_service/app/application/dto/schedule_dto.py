"""
Data Transfer Objects for Application Layer
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class ScheduleItemDTO(BaseModel):
    """Schedule item DTO"""
    id: Optional[UUID] = None
    schedule_id: Optional[UUID] = None
    order_detail_id: UUID
    status: str = "pending"
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    queue: Optional[int] = None

    class Config:
        from_attributes = True


class ScheduleDTO(BaseModel):
    """Schedule DTO"""
    id: Optional[UUID] = None
    driver_id: UUID
    area_code: Optional[str] = None
    scheduled_date: datetime
    status: str = "pending"
    total_orders: int = 0
    completed_orders: int = 0
    failed_orders: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    post_office_id: Optional[UUID] = None
    items: List[ScheduleItemDTO] = []

    class Config:
        from_attributes = True


class CreateScheduleRequest(BaseModel):
    """Request to create schedules"""
    scheduled_date: datetime = Field(..., description="Date for scheduling")
    post_office_id: Optional[UUID] = Field(None, description="Post office ID filter")
    area_code: Optional[str] = Field(None, description="Area code filter")
    driver_ids: Optional[List[UUID]] = Field(None, description="Specific drivers to use")
    order_limit: Optional[int] = Field(None, description="Maximum orders to schedule")
    use_genetic_algorithm: bool = Field(True, description="Use GA optimization")


class ScheduleResponse(BaseModel):
    """Response with schedule data"""
    schedule: ScheduleDTO
    metrics: dict


class BatchScheduleResponse(BaseModel):
    """Response with multiple schedules"""
    schedules: List[ScheduleDTO]
    summary: dict
    optimization_time: Optional[float] = None


class UpdateScheduleRequest(BaseModel):
    """Request to update schedule"""
    status: Optional[str] = None
    add_order_ids: Optional[List[UUID]] = None
    remove_order_ids: Optional[List[UUID]] = None


class DriverWorkloadDTO(BaseModel):
    """Driver workload information"""
    driver_id: UUID
    driver_name: str
    current_orders: int
    scheduled_orders: int
    capacity_percentage: float
    status: str


class OptimizationMetrics(BaseModel):
    """Metrics from optimization process"""
    total_drivers: int
    total_orders: int
    avg_orders_per_driver: float
    optimization_time_seconds: float
    fitness_score: float
    areas_covered: int