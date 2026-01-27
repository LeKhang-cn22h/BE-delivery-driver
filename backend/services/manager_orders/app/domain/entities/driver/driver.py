from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import time

@dataclass
class Driver:
    id: Optional[UUID]
    user_id: UUID
    name: str
    phone: Optional[str]
    status: str
    post_office_id: Optional[UUID]

