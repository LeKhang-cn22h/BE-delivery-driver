# app/application/dto/order_dto.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

class OrderDetailStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    picking = "picking"
    picked_up = "picked_up"
    delivering = "delivering"
    completed = "completed"
    cancelled = "cancelled"

class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    processing = "processing"
    completed = "completed"
    cancelled = "cancelled"

class GeoPointDTO(BaseModel):
    lat: float
    lng: float

    @classmethod
    def from_point_string(cls, p: str):
        # "(lng,lat)" hoặc "(lat,lng)" tùy DB của bạn
        p = p.strip("()")
        a, b = map(float, p.split(","))

        #  Chú ý: Supabase POINT = (x,y) = (lng,lat)
        lng = a
        lat = b

        return cls(lat=lat, lng=lng)


class OrderDetailCreateDTO(BaseModel):
    """DTO cho 1 kiện hàng trong đơn"""
    start_point: str = Field(..., min_length=1, description="Địa chỉ giao hàng")
    address_detail: str = Field(..., min_length=1, description="Chi tiết địa chỉ")
    area_code: str = Field(..., min_length=1, description="Mã khu vực giao")
    location: Optional[GeoPointDTO] = Field(None, description="Tọa độ {lat, lng}")
    price: float = Field(..., gt=0, description="Phí giao kiện này")
    priority_score: int = Field(default=0, description="Độ ưu tiên")

    @field_validator("location", mode="before")
    @classmethod
    def parse_location(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return GeoPointDTO.from_point_string(v)
        return v
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Giá phải lớn hơn 0')
        return v


class OrderCreateDTO(BaseModel):
    """DTO tạo đơn hàng mới"""
    user_id: str = Field(..., min_length=1, description="ID khách hàng")

    # Thông tin lấy hàng
    pickup_point: str = Field(..., min_length=1, description="Địa chỉ lấy hàng")
    pickup_address: str = Field(..., min_length=1, description="Chi tiết địa chỉ lấy")
    pickup_area_code: str = Field(..., min_length=1, description="Mã khu vực lấy")
    pickup_location: Optional[GeoPointDTO]= Field(None, description="Tọa độ lấy hàng")
    pickup_phone: str = Field(..., min_length=1, description="SĐT liên hệ lấy hàng")
    pickup_note: Optional[str] = Field(None, description="Ghi chú khi lấy hàng")

    order_type: str = Field(..., pattern='^(drop_off|pickup)$', description="Loại đơn")


    # Danh sách kiện hàng (tối thiểu 1 kiện)
    order_details: List[OrderDetailCreateDTO] = Field(..., min_items=1, description="Danh sách kiện hàng")

    @field_validator("pickup_location", mode="before")
    @classmethod
    def parse_pickup_location(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return GeoPointDTO.from_point_string(v)
        return v
    @field_validator('order_details')
    @classmethod
    def validate_order_details(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Đơn hàng phải có ít nhất 1 kiện hàng')
        return v


class OrderDetailResponseDTO(BaseModel):
    """Response cho 1 kiện hàng"""
    id: str
    order_id: str
    start_point: str
    address_detail: str
    area_code: str
    price: float
    status: OrderDetailStatus
    priority_score: int


class OrderResponseDTO(BaseModel):
    """Response đơn hàng đầy đủ"""
    id: str
    user_id: str

    # Thông tin lấy hàng
    pickup_point: str
    pickup_address: str
    pickup_area_code: str
    pickup_phone: str
    pickup_note: Optional[str]

    # Trạng thái
    status: OrderStatus
    order_type: str
    created_at: datetime

    # Thống kê kiện hàng
    total_packages: int
    delivered_packages: int
    failed_packages: int
    total_price: float

    # Chi tiết các kiện
    order_details: List[OrderDetailResponseDTO]

    class Config:
        from_attributes = True


class OrderSummaryDTO(BaseModel):
    """Response tóm tắt đơn hàng (dùng cho list)"""
    id: str
    pickup_point: str
    status: OrderStatus
    created_at: datetime
    total_packages: int
    total_price: float

    class Config:
        from_attributes = True
