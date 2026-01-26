from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import time


class PostOfficeCreateDTO(BaseModel):
    code: str
    name: str
    address: str
    ward: Optional[str] = None
    district: Optional[str] = None
    province: Optional[str] = None
    area_codes: List[str]
    phone: Optional[str] = None
    email: Optional[str] = None
    open_time: time
    close_time: time
    working_days: str
    manager_id: Optional[UUID] = None
    status: str = "active"
    location: Optional[List[float]] = None  # [lat, lng]


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