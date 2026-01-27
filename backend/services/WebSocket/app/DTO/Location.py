from pydantic import BaseModel
from typing import Optional, List, Dict
from uuid import UUID
class LocationUpdateDTO(BaseModel):
    lat: float
    lng: float
    speed: Optional[float] = 0
    heading: Optional[float] = 0
    status: Optional[str] = "moving" 
    schedule_id: Optional[UUID] = None
    order_detail_id: Optional[UUID] = None

class LocationResponseDTO(BaseModel):
    driver_id: str
    lat: float
    lng: float
    speed: Optional[float]
    heading: Optional[float]
    status: str
    schedule_id: Optional[str]
    order_detail_id: Optional[str]
    updated_at: str

def parse_point(point_str: str) -> Optional[dict]:
    """Parse PostgreSQL POINT '(lng,lat)' thành dict"""
    if not point_str:
        return None
    coords = point_str.strip("()").split(",")
    return {"lng": float(coords[0]), "lat": float(coords[1])}

def to_point_string(lat: float, lng: float) -> str:
    """Convert lat/lng thành PostgreSQL POINT '(lng,lat)'"""
    return f"({lng},{lat})"