# domain/models.py
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any, Union
from datetime import datetime

class OrderDetail(BaseModel):
    """Model cho order_detail"""
    id: str
    order_id: str
    start_point: str
    status: str
    address_detail: str
    area_code: Optional[str] = None
    location: Optional[Union[str, Dict[str, Any]]] = None
    priority_score: Optional[int] = None

    @field_validator('location', mode='before')
    @classmethod
    def parse_location(cls, v):
        """Parse PostGIS point format '(x,y)' to dict or keep as is"""
        if v is None:
            return None
        if isinstance(v, str):
            # Parse '(10.775658,106.693761)' to dict
            try:
                coords = v.strip('()').split(',')
                if len(coords) == 2:
                    return {
                        'latitude': float(coords[0]),
                        'longitude': float(coords[1])
                    }
            except:
                pass
        return v

    class Config:
        from_attributes = True


class ScheduleItem(BaseModel):
    """Model cho schedule_item"""
    id: str
    schedule_id: str
    order_detail_id: str
    status: str
    queue: int  
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

    class Config:
        from_attributes = True


class Schedule(BaseModel):
    """Model cho schedule"""
    id: str
    driver_id: Optional[str] = None
    scheduled_date: datetime
    area_code: str
    status: str
    total_orders: int
    completed_orders: int = 0
    failed_orders: int = 0
    created_at: Optional[datetime] = None
    post_office_id: str

    class Config:
        from_attributes = True