from pydantic import BaseModel
from typing import List

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