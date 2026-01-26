from pydantic import BaseModel
from typing import List,Optional

class Location(BaseModel):
    lat:float 
    lon:float
    name:Optional[str] = None

class RouteRequest(BaseModel):
    locations:List[Location]
    start_index:int 
    end_index:Optional[int] = None

class OptimizedRoute(BaseModel):
    order: List[int]  # Thứ tự điểm tối ưu
    total_distance: float  # km
    total_duration: float  # giây
    coordinates: List[List[float]]  # [[lng, lat], ...]
    
class RouteResponse(BaseModel):
    success: bool
    route: Optional[OptimizedRoute] = None
    error: Optional[str] = None    