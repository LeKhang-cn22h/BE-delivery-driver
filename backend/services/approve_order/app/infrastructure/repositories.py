from infrastructure.database import get_supabase


class OrderRepository:

    @staticmethod
    def get_new_orders_with_details():
        supabase = get_supabase()

        res = (
            supabase
            .table("orders")
            .select("""
                id,
                post_office_id,
                pickup_area_code,
                status,
                order_details (
                    id,
                    area_code,
                    priority_score,
                    status
                )
            """)
            .eq("status", "NEW")
            .execute()
        )

        return res.data

    @staticmethod
    def update_order_status(order_id: str, status: str):
        supabase = get_supabase()

        return (
            supabase
            .table("orders")
            .update({"status": status})
            .eq("id", order_id)
            .execute()
        )

    @staticmethod
    def update_order_detail_status(order_detail_id: str, status: str):
        supabase = get_supabase()

        return (
            supabase
            .table("order_details")
            .update({"status": status})
            .eq("id", order_detail_id)
            .execute()
        )
