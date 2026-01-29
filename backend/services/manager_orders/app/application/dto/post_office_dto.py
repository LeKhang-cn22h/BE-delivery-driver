from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import time


class PostOfficeCreateDTO(BaseModel):
    code: str = Field(..., description="Mã bưu cục")
    name: str = Field(..., description="Tên bưu cục")
    address: str = Field(..., description="Địa chỉ")
    ward: Optional[str] = None
    district: Optional[str] = None
    province: Optional[str] = None
    area_codes: List[str] = Field(..., description="Danh sách mã khu vực phục vụ")
    phone: Optional[str] = None
    email: Optional[str] = None
    open_time: time = Field(..., description="Giờ mở cửa")
    close_time: time = Field(..., description="Giờ đóng cửa")
    working_days: str = Field(..., description="Ngày làm việc (ví dụ: 'Mon-Sat')")
    manager_id: Optional[UUID] = None
    status: str = Field(default="active", pattern="^(active|inactive)$")
    location: Optional[List[float]] = Field(None, description="[lat, lng]")


class PostOfficeResponseDTO(BaseModel):
    id: UUID
    code: str
    name: str
    address: str
    ward: Optional[str]
    district: Optional[str]
    province: Optional[str]
    area_codes: List[str]
    phone: Optional[str]
    email: Optional[str]
    open_time: time
    close_time: time
    working_days: str
    manager_id: Optional[UUID]
    status: str
    location: Optional[Dict[str, float]] = None  # {"lat": float, "lng": float}

    class Config:
        from_attributes = True


class PostOfficeSummaryDTO(BaseModel):
    """DTO đơn giản cho danh sách bưu cục (dùng cho dropdown)"""
    id: UUID
    code: str
    name: str
    address: str
    area_codes: List[str]
    phone: Optional[str]
    status: str

    class Config:
        from_attributes = True