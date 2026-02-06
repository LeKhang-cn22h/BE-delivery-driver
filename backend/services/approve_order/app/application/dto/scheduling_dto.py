# application/dto/scheduling_dto.py
"""
DTO cho scheduling 
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID

class SchedulingRequest(BaseModel):
    """Request để tạo schedule bằng GA """
    
    # Required fields
    scheduled_date: date
    area_codes: List[str]
    post_office_id: UUID
    
    # Schedule constraints
    max_orders_per_schedule: int = 15
    max_distance_km: float = 40.0
    
    # GA parameters
    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elite_size: int = 5

class ScheduleItemResponse(BaseModel):
    """Response cho một item trong schedule"""
    id: str
    order_detail_id: str
    sequence_number: int
    address: Optional[str] = None
    area_code: Optional[str] = None
    priority_score: Optional[float] = None


class ScheduleResponse(BaseModel):
    """Response cho một schedule đã tạo"""
    id: str
    area_code: str
    scheduled_date: date
    status: str
    total_orders: int
    total_distance_km: Optional[float] = None
    items: List[ScheduleItemResponse] = []
    
    # Driver info (null nếu chưa gán)
    driver_id: Optional[str] = None
    driver_name: Optional[str] = None


class SchedulingResponse(BaseModel):
    """Response tổng hợp sau khi xếp lịch bằng GA"""
    success: bool
    message: str
    
    # Summary
    total_orders_processed: int
    total_schedules_created: int
    
    # GA metrics
    best_fitness_score: Optional[float] = None
    generations_run: Optional[int] = None
    
    # Schedules created
    schedules: List[ScheduleResponse] = []
    
    # Đơn hàng không xếp được
    unassigned_order_ids: List[str] = []
    
    # Warnings
    warnings: List[str] = []

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Đã tạo 3 schedules với 45 đơn hàng",
                "total_orders_processed": 45,
                "total_schedules_created": 3,
                "best_fitness_score": 0.85,
                "generations_run": 100,
                "schedules": [],
                "unassigned_order_ids": [],
                "warnings": []
            }
        }


# ============================================================================
# LEGACY DTOs (for OrderProcessingService - sẽ deprecate)
# ============================================================================

class OrderProcessingResult(BaseModel):
    """DTO cho kết quả xử lý đơn hàng của một vùng"""
    schedule_id: str
    area_code: str
    total_orders: int
    order_detail_ids: List[str]


class BatchProcessingResult(BaseModel):
    """DTO cho kết quả xử lý hàng loạt"""
    total_schedules: int
    total_orders: int
    schedules: List[OrderProcessingResult]


# ============================================================================
# INTERNAL DTOs (dùng trong service/algorithm)
# ============================================================================

class OrderForScheduling(BaseModel):
    """Đơn hàng được format để đưa vào GA"""
    id: str
    order_id: str
    area_code: str
    address: str
    latitude: float
    longitude: float
    priority_score: float = 0.0


class GAConfig(BaseModel):
    """Cấu hình cho Genetic Algorithm"""
    max_orders_per_schedule: int = 15
    max_distance_km: float = 40.0
    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elite_size: int = 5
    
    # Fitness weights
    distance_weight: float = 0.4
    priority_weight: float = 0.3
    balance_weight: float = 0.3


class GAStats(BaseModel):
    """Thống kê sau khi chạy GA"""
    generation: int
    best_fitness: float
    average_fitness: float
    worst_fitness: float
    execution_time_seconds: Optional[float] = None
