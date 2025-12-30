from domain.repositories.order_repository import OrderRepository
from domain.entities.order import Order
from infrastructure.db.supabase_client import supabaseUser


class SupabaseOrderRepository(OrderRepository):

    def get_all(self):
        response = (
            supabaseUser
            .schema("public")
            .table("orders")
            .select("id, latitude, longitude")
            .execute()
        )

        return [
            Order(
                id=row["id"],
                latitude=row["latitude"],
                longitude=row["longitude"]
            )
            for row in response.data
        ]