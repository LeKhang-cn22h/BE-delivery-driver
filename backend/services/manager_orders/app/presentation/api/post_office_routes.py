# app/presentation/api/post_office_routes.py

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/post-offices", tags=["post-offices"])


class PostOfficeDTO(BaseModel):
    id: str
    code: str
    name: str
    address: str
    district: str
    province: str
    phone: str
    open_time: str
    close_time: str
    status: str


@router.get("/active", response_model=List[PostOfficeDTO])
async def get_active_post_offices():
    """
    Lấy danh sách bưu cục đang hoạt động
    Dùng cho dropdown khi khách hàng đặt hàng
    """
    from infrastructure.database.supabase_client import SupabaseClient

    client = SupabaseClient.get_client()

    response = (
        client.schema("delivery")
        .table("post_offices")
        .select("id, code, name, address, district, province, phone, open_time, close_time, status")
        .eq("status", "active")
        .order("name")
        .execute()
    )

    return response.data


@router.get("/{post_office_id}", response_model=PostOfficeDTO)
async def get_post_office(post_office_id: str):
    """Chi tiết một bưu cục"""
    from infrastructure.database.supabase_client import SupabaseClient

    client = SupabaseClient.get_client()

    response = (
        client.schema("delivery")
        .table("post_offices")
        .select("*")
        .eq("id", post_office_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy bưu cục")

    return response.data[0]