# application/dto/__init__.py
"""
DTOs cho application layer
"""

from .scheduling_dto import (
    # Request
    SchedulingRequest,
    
    # Response
    SchedulingResponse,
    ScheduleResponse,
    ScheduleItemResponse,
    
    # Legacy (sẽ deprecate)
    OrderProcessingResult,
    BatchProcessingResult,
    
    # Internal
    OrderForScheduling,
    GAConfig,
    GAStats
)

from .schedule_item_dto import (
    # Request
    UpdateScheduleItemStatusRequest,
    BulkUpdateStatusRequest,
    ReorderItemsRequest,
    
    # Response
    ScheduleItemDetailResponse,
    ScheduleItemWithOrderInfo,
    ScheduleItemsListResponse,
    ScheduleItemStatusSummary,
    
    # Nested
    ScheduleItemSummary,
    NextDeliveryItem,
    DeliveryRoute,
    ItemDeliveryHistory
)

__all__ = [
    # Scheduling
    "SchedulingRequest",
    "SchedulingResponse",
    "ScheduleResponse",
    "ScheduleItemResponse",
    "OrderProcessingResult",
    "BatchProcessingResult",
    "OrderForScheduling",
    "GAConfig",
    "GAStats",
    
    # Schedule Item
    "UpdateScheduleItemStatusRequest",
    "BulkUpdateStatusRequest",
    "ReorderItemsRequest",
    "ScheduleItemDetailResponse",
    "ScheduleItemWithOrderInfo",
    "ScheduleItemsListResponse",
    "ScheduleItemStatusSummary",
    "ScheduleItemSummary",
    "NextDeliveryItem",
    "DeliveryRoute",
    "ItemDeliveryHistory",
]
