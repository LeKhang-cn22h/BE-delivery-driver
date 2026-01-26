from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID
from datetime import time

@dataclass
class PostOffice:
    id: Optional[UUID]
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
    location:Optional[dict] = None # e.g., {"latitude": float, "longitude": float}
