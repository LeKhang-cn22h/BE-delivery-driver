from infrastructure.repositories import OrderRepository
from collections import defaultdict


class ApproveOrderService:

    @staticmethod
    def approve_orders_by_area():
        orders = OrderRepository.get_new_orders_with_details()

        if not orders:
            return {"message": "No new orders"}

        grouped_by_area = defaultdict(list)

        # 1. Gom đơn theo area_code
        for order in orders:
            for detail in order.get("order_details", []):
                area_code = detail["area_code"]
                grouped_by_area[area_code].append({
                    "order_id": order["id"],
                    "order_detail_id": detail["id"],
                    "post_office_id": order["post_office_id"],
                })

        # 2. Duyệt và cập nhật trạng thái
        for area_code, items in grouped_by_area.items():
            for item in items:
                OrderRepository.update_order_detail_status(
                    item["order_detail_id"],
                    "APPROVED"
                )

                OrderRepository.update_order_status(
                    item["order_id"],
                    "APPROVED"
                )

        return {
            "approved_areas": list(grouped_by_area.keys()),
            "total_orders": len(orders)
        }
