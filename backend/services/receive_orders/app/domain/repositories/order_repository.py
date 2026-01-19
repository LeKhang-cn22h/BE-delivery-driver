# app/domain/repositories/order_repository.py
from infrastructure.database import SupabaseClient
from typing import Optional


class OrderRepository:
    def __init__(self):
        self.supabase = SupabaseClient().get_client()
        self.table_name = "orders"
        self.schema = "receive_orders"

    def create(self, order_data: dict):
        result = (
            self.supabase
            .schema(self.schema)
            .from_(self.table_name)
            .insert({
                "priority": order_data.get("priority", "normal"),
                "customer_name": order_data["customer_name"],
                "customer_phone": order_data["customer_phone"],
                "pickup_address": order_data["pickup_address"],
                "delivery_address": order_data["delivery_address"],
                "items": order_data["items"],
                "total_amount": order_data.get("total_amount"),
                "notes": order_data.get("notes", ""),
                "created_by": order_data.get("created_by")
            })
            .execute()
        )

        return result.data[0] if result.data else None

    def find_by_id(self, order_id: str):
        result = (
            self.supabase
            .schema(self.schema)
            .from_(self.table_name)
            .select("*")
            .eq("id", order_id)
            .single()
            .execute()
        )

        return result.data if result.data else None

    def find_pending_by_priority(self, priority: Optional[str] = None):
        query = (
            self.supabase
            .schema(self.schema)
            .from_(self.table_name)
            .select("*")
            .eq("status", "pending")
        )

        if priority:
            query = query.eq("priority", priority)

        result = query.order("created_at", desc=True).execute()
        return result.data if result.data else []

    def update_status(self, order_id: str, status: str):
        result = (
            self.supabase
            .schema(self.schema)
            .from_(self.table_name)
            .update({"status": status})
            .eq("id", order_id)
            .execute()
        )

        return result.data[0] if result.data else None
