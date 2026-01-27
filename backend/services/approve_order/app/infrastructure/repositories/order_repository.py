from typing import List
from supabase import Client
from domain.models import OrderDetail


class OrderRepository:
    """Repository cho Order với Supabase"""

    def __init__(self, supabase_client: Client, schema: str = "public"):
        self.db = supabase_client
        self.schema = schema

    async def get_pending_order_details_by_post_office(
            self,
            post_office_id: str
    ) -> List[OrderDetail]:
        """Lấy tất cả order_details pending của bưu cục"""
        try:
            response = (
                self.db.schema(self.schema)
                .table("order_details")
                .select("""
                    *,
                    orders!inner(
                        id,
                        post_office_id,
                        pickup_area_code
                    )
                """)
                .eq("status", "pending")
                .eq("orders.post_office_id", post_office_id)
                .order("created_at", desc=False)
                .execute()
            )

            # Transform data to include area_code
            order_details = []
            for item in response.data:
                od = OrderDetail(**{
                    **item,
                    'area_code': item['orders']['pickup_area_code']
                })
                order_details.append(od)

            return order_details

        except Exception as e:
            raise Exception(f"Lỗi khi lấy pending orders: {str(e)}")

    async def get_pending_order_details_by_area(
            self,
            post_office_id: str,
            area_code: str
    ) -> List[OrderDetail]:
        """Lấy order_details pending của một vùng cụ thể"""
        try:
            response = (
                self.db.schema(self.schema)
                .table("order_details")
                .select("""
                    *,
                    orders!inner(
                        id,
                        post_office_id,
                        pickup_area_code
                    )
                """)
                .eq("status", "pending")
                .eq("orders.post_office_id", post_office_id)
                .eq("orders.pickup_area_code", area_code)
                .order("created_at", desc=False)
                .execute()
            )

            order_details = []
            for item in response.data:
                od = OrderDetail(**{
                    **item,
                    'area_code': item['orders']['pickup_area_code']
                })
                order_details.append(od)

            return order_details

        except Exception as e:
            raise Exception(f"Lỗi khi lấy orders theo vùng: {str(e)}")

    async def update_order_details_status(
            self,
            order_detail_ids: List[str],
            status: str
    ) -> int:
        """Cập nhật status cho nhiều order_details"""
        try:
            response = (
                self.db.schema(self.schema)
                .table("order_details")
                .update({"status": status})
                .in_("id", order_detail_ids)
                .execute()
            )
            return len(response.data)
        except Exception as e:
            raise Exception(f"Lỗi khi cập nhật status: {str(e)}")