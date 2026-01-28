from uuid import UUID
from typing import List,Optional

from domain.entities.driver.driver import Driver
from domain.repositories.driver_repository import DriverRepository
from infrastructure.database.supabase_client import SupabaseClient

class SupabaseDriverRepository(DriverRepository):
    def __init__(self):
        self.supabase = SupabaseClient.get_client()

    def _to_entity(self,data:dict) -> Driver:
        return Driver(
            id=UUID(data["id"]),
            user_id=UUID(data["user_id"]),
            name=data["name"],
            phone=data.get("phone"),
            status=data["status"],
            post_office_id=UUID(data["post_office_id"]) if data.get("post_office_id") else None
        )
    
    def get_by_id(self,driver_id:UUID) -> Optional[Driver]:
        res =(
            self.supabase
            .schema("delivery")
            .table("drivers")
            .select("*")
            .eq("id",str(driver_id))
            .single()
            .execute()
        )
        return self._to_entity(res.data) if res.data else None
    
    def get_by_post_office_id(self, post_office_id):
        res =(
            self.supabase
            .schema("delivery")
            .table("drivers")
            .select("id,user_id,name,phone,status")
            .eq("post_office_id",str(post_office_id))
            .execute()
        )
        return [self._to_entity(row) for row in res.data] if res.data else []
    
    def get_by_status(self, status:str):
        res=(
            self.supabase
            .schema("delivery")
            .table("drivers")
            .select("id,user_id,name,phone,status")
            .eq("status",status)
            .execute()
        )
        return [self._to_entity(row) for row in res.data] if res.data else []
    
    def create(self, driver:Driver)->Optional[Driver]:
        res=(
            self.supabase
            .schema("delivery")
            .table("drivers")
            .insert({
                "user_id": str(driver.user_id),
                "name": driver.name,
                "phone": driver.phone,
                "status": driver.status,
                "post_office_id": str(driver.post_office_id) if driver.post_office_id else None
            })
            .execute()
        )
        return self._to_entity(res.data[0]) if res.data else None
    
    def update(self, driver:Driver) -> Optional[Driver]:
        res =(
            self.supabase
            .schema("delivery")
            .table("drivers")
            .update({
                "name": driver.name,
                "phone": driver.phone,
                "post_office_id": str(driver.post_office_id) if driver.post_office_id else None
            })
            .eq("id",str(driver.id))
            .execute()
        )
        return self._to_entity(res.data[0]) if res.data else None

    def update_status(self, driver) -> Driver:
        res =(
            self.supabase
            .schema("delivery")
            .table("drivers")
            .update({
                "status": driver.status
            })
            .eq("id",str(driver.id))
            .execute()
        )  
        return self._to_entity(res.data[0]) if res.data else None  