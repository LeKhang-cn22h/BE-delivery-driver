# application/dto/schedule_dto.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


# ============================================================================
# REQUEST DTOs
# ============================================================================

class CreateScheduleRequest(BaseModel):
    """Request để tạo schedule thủ công"""
    post_office_id: str
    area_code: str
    scheduled_date: datetime
    driver_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "post_office_id": "81f4b721-e51f-4e66-a91e-e67130dcf013",
                "area_code": "HCM-Q3",
                "scheduled_date": "2026-01-28T08:00:00",
                "driver_id": None
            }
        }


class UpdateScheduleStatusRequest(BaseModel):
    """Request để cập nhật status của schedule"""
    status: str = Field(
        ...,
        description="Status mới",
        pattern="^(draft|confirmed|in_progress|completed)$"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "in_progress"
            }
        }


class AssignDriverRequest(BaseModel):
    """Request để gán tài xế cho schedule"""
    driver_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "driver_id": "driver-123-abc"
            }
        }


# ============================================================================
# RESPONSE DTOs
# ============================================================================

class ScheduleResponse(BaseModel):
    """Response cơ bản cho schedule"""
    id: str
    driver_id: Optional[str]
    scheduled_date: date
    area_code: str
    status: str
    total_orders: int
    completed_orders: int
    failed_orders: int
    post_office_id: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "sch-123-abc",
                "driver_id": None,
                "scheduled_date": "2026-01-28",
                "area_code": "HCM-Q3",
                "status": "confirmed",
                "total_orders": 5,
                "completed_orders": 0,
                "failed_orders": 0,
                "post_office_id": "81f4b721-e51f-4e66-a91e-e67130dcf013",
                "created_at": "2026-01-27T08:00:00"
            }
        }


class ScheduleDetailResponse(ScheduleResponse):
    """Response chi tiết bao gồm danh sách order_details"""
    items: list = []

    class Config:
        from_attributes = True


class ScheduleSummaryResponse(BaseModel):
    """Response tóm tắt cho schedule (dùng trong list)"""
    id: str
    area_code: str
    scheduled_date: date
    status: str
    total_orders: int
    completed_orders: int
    driver_id: Optional[str]

    class Config:
        from_attributes = True


class ScheduleStatsResponse(BaseModel):
    """Response thống kê schedule"""
    total_schedules: int
    by_status: dict
    by_area: dict

    class Config:
        json_schema_extra = {
            "example": {
                "total_schedules": 10,
                "by_status": {
                    "confirmed": 5,
                    "in_progress": 3,
                    "completed": 2
                },
                "by_area": {
                    "HCM-Q3": 4,
                    "HCM-Q1": 6
                }
            }
        }


# ============================================================================
# NESTED DTOs (dùng trong responses khác)
# ============================================================================

class ScheduleInOrderProcessingResult(BaseModel):
    """Schedule info trong kết quả xử lý đơn hàng"""
    schedule_id: str
    area_code: str
    scheduled_date: date
    status: str
    total_orders: int

    class Config:
        from_attributes = True


class ScheduleProgress(BaseModel):
    """Tiến độ của schedule"""
    schedule_id: str
    total_orders: int
    completed_orders: int
    failed_orders: int
    in_progress_orders: int
    completion_percentage: float

    class Config:
        json_schema_extra = {
            "example": {
                "schedule_id": "sch-123",
                "total_orders": 10,
                "completed_orders": 7,
                "failed_orders": 1,
                "in_progress_orders": 2,
                "completion_percentage": 70.0
            }
        }