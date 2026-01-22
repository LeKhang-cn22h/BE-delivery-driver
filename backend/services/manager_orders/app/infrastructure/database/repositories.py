from typing import List, Optional
from datetime import datetime
from uuid import UUID
import asyncpg
from asyncpg import Pool


class OrderRepository:
    """Repository class for handling database operations related to orders"""
    
    def __init__(self, pool: Pool):
        self.pool = pool
    
    async def create_order(
        self, 
        user_id: UUID, 
        pickup_point: str, 
        status: str = "pending"
    ) -> dict:
        """Create a new order"""
        query = """
            INSERT INTO orders (user_id, pickup_point, status, created_at)
            VALUES ($1, $2, $3, NOW())
            RETURNING id, user_id, pickup_point, status, created_at
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, pickup_point, status)
            return dict(row)
    
    async def get_order_by_id(self, order_id: UUID) -> Optional[dict]:
        """Get order by ID"""
        query = """
            SELECT id, user_id, pickup_point, status, created_at
            FROM orders
            WHERE id = $1
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, order_id)
            return dict(row) if row else None
    
    async def get_orders_by_user(self, user_id: UUID) -> List[dict]:
        """Get all orders for a specific user"""
        query = """
            SELECT id, user_id, pickup_point, status, created_at
            FROM orders
            WHERE user_id = $1
            ORDER BY created_at DESC
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]
    
    async def update_order_status(self, order_id: UUID, status: str) -> bool:
        """Update order status"""
        query = """
            UPDATE orders
            SET status = $1
            WHERE id = $2
            RETURNING id
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, status, order_id)
            return row is not None


class OrderDetailRepository:
    """Repository class for handling order details operations"""
    
    def __init__(self, pool: Pool):
        self.pool = pool
    
    async def create_order_detail(
        self,
        order_id: UUID,
        start_point: str,
        price: float,
        status: str = "pending"
    ) -> dict:
        """Create a new order detail"""
        query = """
            INSERT INTO order_details (order_id, start_point, price, status)
            VALUES ($1, $2, $3, $4)
            RETURNING id, order_id, start_point, price, status
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, order_id, start_point, price, status)
            return dict(row)
    
    async def get_order_details_by_order_id(self, order_id: UUID) -> List[dict]:
        """Get all order details for a specific order"""
        query = """
            SELECT id, order_id, start_point, price, status
            FROM order_details
            WHERE order_id = $1
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, order_id)
            return [dict(row) for row in rows]
    
    async def update_order_detail_status(
        self, 
        order_detail_id: UUID, 
        status: str
    ) -> bool:
        """Update order detail status"""
        query = """
            UPDATE order_details
            SET status = $1
            WHERE id = $2
            RETURNING id
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, status, order_detail_id)
            return row is not None


class OrderDetailUrgentRepository:
    """Repository class for handling urgent order details operations"""
    
    def __init__(self, pool: Pool):
        self.pool = pool
    
    async def create_urgent_order_detail(
        self,
        order_detail_id: UUID,
        start_point: str,
        urgent_time: str,  # interval type
        price: float,
        status: str = "pending"
    ) -> dict:
        """Create a new urgent order detail"""
        query = """
            INSERT INTO order_detail_urgent 
            (order_detail_id, start_point, urgent_time, price, status)
            VALUES ($1, $2, $3::interval, $4, $5)
            RETURNING id, order_detail_id, start_point, urgent_time, price, status
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query, 
                order_detail_id, 
                start_point, 
                urgent_time, 
                price, 
                status
            )
            return dict(row)
    
    async def get_urgent_order_detail_by_id(
        self, 
        urgent_detail_id: UUID
    ) -> Optional[dict]:
        """Get urgent order detail by ID"""
        query = """
            SELECT id, order_detail_id, start_point, urgent_time, price, status
            FROM order_detail_urgent
            WHERE id = $1
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, urgent_detail_id)
            return dict(row) if row else None
    
    async def get_urgent_orders_by_detail_id(
        self, 
        order_detail_id: UUID
    ) -> List[dict]:
        """Get all urgent order details for a specific order detail"""
        query = """
            SELECT id, order_detail_id, start_point, urgent_time, price, status
            FROM order_detail_urgent
            WHERE order_detail_id = $1
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, order_detail_id)
            return [dict(row) for row in rows]
    
    async def update_urgent_order_status(
        self, 
        urgent_detail_id: UUID, 
        status: str
    ) -> bool:
        """Update urgent order detail status"""
        query = """
            UPDATE order_detail_urgent
            SET status = $1
            WHERE id = $2
            RETURNING id
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, status, urgent_detail_id)
            return row is not None


class OrderService:
    """Service class combining all repositories for complete order operations"""
    
    def __init__(self, pool: Pool):
        self.orders = OrderRepository(pool)
        self.order_details = OrderDetailRepository(pool)
        self.urgent_details = OrderDetailUrgentRepository(pool)
    
    async def get_full_order(self, order_id: UUID) -> Optional[dict]:
        """Get complete order information including all details and urgent details"""
        order = await self.orders.get_order_by_id(order_id)
        if not order:
            return None
        
        details = await self.order_details.get_order_details_by_order_id(order_id)
        
        for detail in details:
            urgent = await self.urgent_details.get_urgent_orders_by_detail_id(
                detail['id']
            )
            detail['urgent_details'] = urgent
        
        order['details'] = details
        return order


# Database connection setup
async def create_db_pool(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str
) -> Pool:
    """Create database connection pool"""
    return await asyncpg.create_pool(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        min_size=10,
        max_size=20
    )


# Example usage
async def example_usage():
    """Example of how to use the repositories"""
    
    # Create connection pool
    pool = await create_db_pool(
        host='localhost',
        port=5432,
        database='your_database',
        user='your_user',
        password='your_password'
    )
    
    # Initialize service
    service = OrderService(pool)
    
    # Create an order
    user_id = UUID('12345678-1234-5678-1234-567812345678')
    new_order = await service.orders.create_order(
        user_id=user_id,
        pickup_point='123 Main Street',
        status='pending'
    )
    
    # Create order detail
    order_detail = await service.order_details.create_order_detail(
        order_id=new_order['id'],
        start_point='456 Start Avenue',
        price=29.99,
        status='pending'
    )
    
    # Create urgent order detail
    urgent_detail = await service.urgent_details.create_urgent_order_detail(
        order_detail_id=order_detail['id'],
        start_point='789 Urgent Street',
        urgent_time='2 hours',
        price=49.99,
        status='urgent'
    )
    
    # Get full order information
    full_order = await service.get_full_order(new_order['id'])
    print(full_order)
    
    # Close pool
    await pool.close()