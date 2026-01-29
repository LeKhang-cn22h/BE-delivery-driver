# infrastructure/repositories/order_repository.py
from typing import List, Dict, Optional
from supabase import Client
from domain.models import OrderDetail
from collections import defaultdict


class OrderRepository:
    """Repository cho Order và OrderDetail với Supabase"""

    def __init__(self, supabase_client: Client, schema: str = "delivery"):
        self.db = supabase_client
        self.schema = schema

    async def get_pending_orders_by_post_office(
            self,
            post_office_id: str
    ) -> List[OrderDetail]:
        """
        Lấy tất cả order_details có status='pending' của một bưu cục
        Sắp xếp theo priority_score giảm dần

        Logic:
        - orders (1) -> order_details (nhiều)
        - Filter: orders.post_office_id = ? AND order_details.status = 'pending'
        """
        try:
            response = (
                self.db.schema(self.schema)
                .table("order_details")
                .select("""
                    id,
                    order_id,
                    start_point,
                    status,
                    address_detail,
                    area_code,
                    location,
                    priority_score,
                    orders!inner(
                        id,
                        user_id,
                        post_office_id
                    )
                """)
                .eq("status", "pending")
                .eq("orders.post_office_id", post_office_id)
                .order("priority_score", desc=True)
                .execute()
            )

            return [OrderDetail(**item) for item in response.data]

        except Exception as e:
            raise Exception(f"Lỗi khi lấy pending orders: {str(e)}")

    async def get_all_orders_with_priority(
            self,
            post_office_id: str,
            status: Optional[str] = None
    ) -> List[OrderDetail]:
        """
        Lấy tất cả order_details với priority_score của một bưu cục

        Logic:
        - Query từ order_details
        - JOIN với orders để filter theo post_office_id
        - orders.post_office_id xác định bưu cục
        - order_details.area_code xác định vùng giao hàng
        - order_details.priority_score xác định độ ưu tiên

        Args:
            post_office_id: ID bưu cục (từ bảng orders)
            status: Lọc theo status của order_details (None = lấy tất cả)

        Returns:
            List OrderDetail đã sắp xếp theo priority_score giảm dần
        """
        try:
            query = (
                self.db.schema(self.schema)
                .table("order_details")
                .select("""
                    id,
                    order_id,
                    start_point,
                    status,
                    address_detail,
                    area_code,
                    location,
                    priority_score,
                    orders!inner(
                        id,
                        user_id,
                        post_office_id
                    )
                """)
                .eq("orders.post_office_id", post_office_id)
                .order("priority_score", desc=True)
            )

            # Lọc theo status nếu có
            if status:
                query = query.eq("status", status)

            response = query.execute()

            return [OrderDetail(**item) for item in response.data]

        except Exception as e:
            raise Exception(f"Lỗi khi lấy orders với priority: {str(e)}")

    async def get_orders_grouped_by_area(
            self,
            post_office_id: str,
            status: str = "pending"
    ) -> Dict[str, List[OrderDetail]]:
        """
        Lấy orders và nhóm theo area_code
        Mỗi area sẽ có danh sách orders đã sắp xếp theo priority

        Returns:
            Dict với key là area_code, value là List[OrderDetail]
        """
        try:
            # Lấy tất cả orders
            orders = await self.get_all_orders_with_priority(
                post_office_id=post_office_id,
                status=status
            )

            # Nhóm theo area_code
            grouped = defaultdict(list)
            for order in orders:
                if order.area_code:
                    grouped[order.area_code].append(order)

            return dict(grouped)

        except Exception as e:
            raise Exception(f"Lỗi khi nhóm orders theo area: {str(e)}")

    async def get_orders_by_area(
            self,
            post_office_id: str,
            area_code: str,
            status: str = "pending"
    ) -> List[OrderDetail]:
        """
        Lấy orders của một vùng cụ thể

        Logic:
        - order_details.area_code xác định vùng
        - orders.post_office_id xác định bưu cục
        - order_details.status xác định trạng thái
        """
        try:
            response = (
                self.db.schema(self.schema)
                .table("order_details")
                .select("""
                    id,
                    order_id,
                    start_point,
                    status,
                    address_detail,
                    area_code,
                    location,
                    priority_score,
                    orders!inner(
                        id,
                        user_id,
                        post_office_id
                    )
                """)
                .eq("status", status)
                .eq("area_code", area_code)
                .eq("orders.post_office_id", post_office_id)
                .order("priority_score", desc=True)
                .execute()
            )

            # Trả về empty list thay vì throw error
            if not response.data:
                return []

            # Parse từng item
            result = []
            for item in response.data:
                try:
                    result.append(OrderDetail(**item))
                except Exception as parse_error:
                    print(f"Error parsing item: {item}")
                    print(f"Parse error: {str(parse_error)}")
                    raise

            return result

        except Exception as e:
            # Log chi tiết hơn
            import traceback
            print(f"Error in get_orders_by_area:")
            print(f"  post_office_id: {post_office_id}")
            print(f"  area_code: {area_code}")
            print(f"  status: {status}")
            print(f"  Error: {str(e)}")
            print(f"  Traceback: {traceback.format_exc()}")
            raise Exception(f"Lỗi khi lấy orders theo area: {str(e)}")

    async def update_order_details_status(
            self,
            order_detail_ids: List[str],
            status: str
    ) -> List[OrderDetail]:
        """Cập nhật status cho nhiều order_details"""
        try:
            response = (
                self.db.schema(self.schema)
                .table("order_details")
                .update({"status": status})
                .in_("id", order_detail_ids)
                .execute()
            )

            if not response.data:
                raise Exception("Không thể cập nhật order details")

            return [OrderDetail(**item) for item in response.data]

        except Exception as e:
            raise Exception(f"Lỗi khi cập nhật status: {str(e)}")

    async def get_order_detail_by_id(self, order_detail_id: str) -> OrderDetail:
        """Lấy một order_detail theo ID"""
        try:
            response = (
                self.db.schema(self.schema)
                .table("order_details")
                .select("*")
                .eq("id", order_detail_id)
                .single()
                .execute()
            )

            return OrderDetail(**response.data)

        except Exception as e:
            raise Exception(f"Lỗi khi lấy order detail: {str(e)}")

    async def get_pending_order_details_by_area(
            self,
            post_office_id: str,
            area_code: str
    ) -> List[OrderDetail]:
        """
        Lấy order_details pending của một vùng cụ thể
        (Alias cho get_orders_by_area với status='pending')
        """
        return await self.get_orders_by_area(
            post_office_id=post_office_id,
            area_code=area_code,
            status="pending"
        )

