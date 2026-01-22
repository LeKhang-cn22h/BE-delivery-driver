from infrastructure.database.session import engine

class OrderRepository:

    def create(self, user_id: str, pickup_point: str):
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO orders (user_id, pickup_point, status)
                    VALUES (:user_id, :pickup_point, 'pending')
                    RETURNING id
                """),
                {
                    "user_id": user_id,
                    "pickup_point": pickup_point
                }
            )
            return result.scalar()

    def update_status(self, order_id: str, status: str) -> bool:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    UPDATE orders
                    SET status = :status
                    WHERE id = :order_id
                """),
                {"order_id": order_id, "status": status}
            )
            return result.rowcount > 0

    def cancel(self, order_id: str) -> bool:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    UPDATE orders
                    SET status = 'cancelled'
                    WHERE id = :order_id
                      AND status NOT IN ('completed', 'cancelled')
                """),
                {"order_id": order_id}
            )
            return result.rowcount > 0
