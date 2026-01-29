from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date, time
from uuid import UUID


class DriverAvailability(BaseModel):
    """Thông tin tài xế có sẵn"""
    driver_id: UUID
    name: str
    phone: str
    status: str
    post_office_id: UUID
    current_location: Optional[tuple[float, float]] = None  # (lat, lon)


class OrderDetailForScheduling(BaseModel):
    """Thông tin đơn hàng cần xếp lịch"""
    id: UUID
    order_id: UUID
    start_point: str
    address_detail: Optional[str] = None
    area_code: str
    location: tuple[float, float]  # (lat, lon)
    priority_score: int = 0
    pickup_location: Optional[tuple[float, float]] = None  # Điểm lấy hàng


class ShiftConfig(BaseModel):
    """Cấu hình ca làm việc"""
    shift_name: str
    start_time: time
    end_time: time
    max_orders_per_driver: int = 20
    max_distance_km: float = 50.0  # Khoảng cách tối đa mà tài xế có thể đi trong 1 ca


class SchedulingRequest(BaseModel):
    """Request để xếp lịch"""
    scheduled_date: date
    area_codes: List[str]
    post_office_id: UUID
    shift_configs: List[ShiftConfig]
    # GA Parameters
    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elite_size: int = 5


class ScheduleAssignment(BaseModel):
    """Phân công đơn hàng cho tài xế"""
    driver_id: UUID
    driver_name: str
    shift_name: str
    order_detail_ids: List[UUID]
    total_orders: int
    estimated_distance_km: float
    estimated_time_hours: float
    route_sequence: List[int]  # Thứ tự giao hàng tối ưu


class SchedulingResponse(BaseModel):
    """Kết quả xếp lịch"""
    schedule_id: UUID
    scheduled_date: date
    post_office_id: UUID
    assignments: List[ScheduleAssignment]
    total_orders_scheduled: int
    unassigned_orders: List[UUID]
    fitness_score: float
    algorithm_info: dict


class GeneticAlgorithmStats(BaseModel):
    """Thống kê thuật toán GA"""
    generation: int
    best_fitness: float
    average_fitness: float
    worst_fitness: float
    execution_time_seconds: float