from uuid import UUID
from typing import List, Optional

from domain.entities.post_offices.post_office import PostOffice
from domain.repositories.post_office_repository import PostOfficeRepository
from infrastructure.database.supabase_client import SupabaseClient
from datetime import time


class SupabasePostOfficeRepository(PostOfficeRepository):

    def __init__(self):
        self.supabase = SupabaseClient.get_client()


    def _parse_point(self, point: str | None):
        if not point:
            return None

        lng, lat = point.strip("()").split(",")
        return {
            "lat": float(lat),
            "lng": float(lng),
        }

    def _to_entity(self, data: dict) -> PostOffice:
        return PostOffice(
        id=UUID(data["id"]),
        code=data["code"],
        name=data["name"],
        address=data["address"],
        ward=data.get("ward"),
        district=data.get("district"),
        province=data.get("province"),
        area_codes=data["area_codes"],
        phone=data.get("phone"),
        email=data.get("email"),
        open_time=time.fromisoformat(data["open_time"]),
        close_time=time.fromisoformat(data["close_time"]),
        working_days=data["working_days"],
        manager_id=UUID(data["manager_id"]) if data.get("manager_id") else None,
        status=data["status"],
        location=self._parse_point(data.get("location"))
    )

    def get_by_id(self, post_office_id: UUID) -> Optional[PostOffice]:
        res = (
            self.supabase
            .schema("delivery")
            .table("post_offices")
            .select("*")
            .eq("id", str(post_office_id))
            .single()
            .execute()
        )
        return self._to_entity(res.data) if res.data else None

    def get_by_area_code(self, area_code: str) -> List[PostOffice]:
        res = (
            self.supabase
            .schema("delivery")
            .table("post_offices")
            .select("*")
            .contains("area_codes", [area_code])
            .execute()
        )
        return [self._to_entity(item) for item in res.data]

    def create(self, post_office: PostOffice) -> PostOffice:
        # Convert entity to dict, loại bỏ id nếu None
        data = {
            "code": post_office.code,
            "name": post_office.name,
            "address": post_office.address,
            "ward": post_office.ward,
            "district": post_office.district,
            "province": post_office.province,
            "area_codes": post_office.area_codes,
            "phone": post_office.phone,
            "location": (
                f"({post_office.location.lng},{post_office.location.lat})"
                if post_office.location else None
            ),
            "email": post_office.email,
            "open_time": str(post_office.open_time),
            "close_time": str(post_office.close_time),
            "working_days": post_office.working_days,
            "manager_id": str(post_office.manager_id) if post_office.manager_id else None,
            "status": post_office.status
        }
        
        res = self.supabase.schema("delivery").table("post_offices").insert(data).execute()
        return self._to_entity(res.data[0])

    def update(self, post_office_id: UUID, status: str) -> None:
        (
            self.supabase
            .schema("delivery")
            .table("post_offices")
            .update({"status": status})
            .eq("id", str(post_office_id))
            .execute()
        )