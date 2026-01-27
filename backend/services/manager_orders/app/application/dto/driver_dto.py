import datetime
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class DriverDTO(BaseModel):
    user_id: UUID
    name: str
    phone: Optional[str] = None
    status: str
    post_office_id: Optional[UUID] = None

    class Config:
        from_attributes = True

class DriverResponseDTO(DriverDTO):
    id: UUID
    created_at: datetime

class DriverDetailDTO(DriverDTO):
    created_at: Optional[datetime] = None

class DriverUpdateDTO(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    post_office_id:Optional[UUID]=None

