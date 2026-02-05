import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

import psycopg2
from psycopg2.extras import execute_batch
from minio import Minio

# =====================
# LOGGING SETUP
# =====================
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - [ETL] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================
# CONFIG
# =====================
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres_warehouse"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "warehouse"),
    "user": os.getenv("POSTGRES_USER", "admin"),
    "password": os.getenv("POSTGRES_PASSWORD", "admin123")
}

MINIO_CONFIG = {
    "endpoint": os.getenv("MINIO_ENDPOINT", "minio:9000"),
    "access_key": os.getenv("MINIO_ACCESS_KEY", "admin"),
    "secret_key": os.getenv("MINIO_SECRET_KEY", "admin123"),
    "bucket": os.getenv("MINIO_BUCKET", "datalake")
}

PROCESSING_INTERVAL = int(os.getenv("PROCESSING_INTERVAL", "300"))  # 5 phút


# =====================
# DATABASE SETUP
# =====================
def init_database():
    """Create warehouse tables if not exist"""
    logger.info("Initializing database schema...")

    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()

    # Drop old tables if exist (để tránh conflict)
    cur.execute("DROP TABLE IF EXISTS fact_orders CASCADE")
    cur.execute("DROP TABLE IF EXISTS dim_areas CASCADE")
    cur.execute("DROP TABLE IF EXISTS fact_routes CASCADE")

    # Bảng fact_orders
    cur.execute("""
        CREATE TABLE fact_orders (
            order_id VARCHAR(100) PRIMARY KEY,
            user_id VARCHAR(100),
            driver_id VARCHAR(100),
            pickup_area_code VARCHAR(50),
            total_amount DECIMAL(10, 2),
            status VARCHAR(50),
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bảng dim_areas
    cur.execute("""
        CREATE TABLE dim_areas (
            area_code VARCHAR(50) PRIMARY KEY,
            area_name VARCHAR(200),
            total_deliveries INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bảng fact_routes
    cur.execute("""
        CREATE TABLE fact_routes (
            id SERIAL PRIMARY KEY,
            order_id VARCHAR(100),
            pickup_area VARCHAR(50),
            delivery_area VARCHAR(50),
            created_at TIMESTAMP,
            UNIQUE(order_id, pickup_area, delivery_area)
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

    logger.info("Database schema initialized!")
# =====================
# ETL FUNCTIONS
# =====================
def get_minio_client() -> Minio:
    """Create MinIO client"""
    return Minio(
        MINIO_CONFIG["endpoint"],
        access_key=MINIO_CONFIG["access_key"],
        secret_key=MINIO_CONFIG["secret_key"],
        secure=False
    )


def extract_orders_from_minio() -> List[Dict[str, Any]]:
    """Extract all order JSON files from MinIO"""
    logger.info("Extracting orders from MinIO...")

    client = get_minio_client()
    bucket = MINIO_CONFIG["bucket"]

    orders = []

    try:
        objects = client.list_objects(bucket, prefix="orders/", recursive=True)

        for obj in objects:
            if not obj.object_name.endswith(".json"):
                continue

            try:
                response = client.get_object(bucket, obj.object_name)
                data = json.loads(response.read())
                orders.append(data)
                response.close()
                response.release_conn()
            except Exception as e:
                logger.error(f"Error reading {obj.object_name}: {e}")
                continue

        logger.info(f"Extracted {len(orders)} orders from MinIO")
        return orders

    except Exception as e:
        logger.error(f"MinIO extraction error: {e}")
        return []


def load_to_warehouse(orders: List[Dict[str, Any]]):
    """Load orders into Postgres warehouse"""
    if not orders:
        logger.info("No orders to load")
        return

    logger.info(f"Loading {len(orders)} orders to warehouse...")

    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()

    fact_orders_data = []
    fact_routes_data = []
    area_updates = {}

    for order in orders:
        try:
            # Get payload
            payload = order.get("payload", {})

            # ===== FIX: Extract correct fields from JSON =====
            order_id = payload.get("id")  # ← Đổi từ "order_id" thành "id"
            user_id = payload.get("user_id")
            driver_id = payload.get("driver_id")  # Có thể null ban đầu
            pickup_area = payload.get("pickup_area_code")

            # Total amount (tính từ order_details nếu cần)
            total = float(payload.get("total_amount", 0) or 0)

            status = payload.get("status", "pending")
            created = payload.get("created_at")
            updated = payload.get("updated_at")  # Có thể null

            # Skip if missing critical fields
            if not order_id:
                logger.warning(f"Skipping order with missing order_id")
                continue

            fact_orders_data.append((
                order_id, user_id, driver_id, pickup_area,
                total, status, created, updated
            ))

            # Extract routes for Apriori analysis
            order_details = payload.get("order_details", [])

            for detail in order_details:
                delivery_area = detail.get("area_code")

                if delivery_area and pickup_area:
                    fact_routes_data.append((
                        order_id, pickup_area, delivery_area, created
                    ))

                    # Count deliveries per area
                    area_updates[delivery_area] = area_updates.get(delivery_area, 0) + 1

        except Exception as e:
            logger.error(f"Error parsing order: {e}")
            logger.error(f"Order data: {json.dumps(order, indent=2)}")
            continue

    # Insert into fact_orders (UPSERT)
    if fact_orders_data:
        try:
            execute_batch(cur, """
                INSERT INTO fact_orders 
                (order_id, user_id, driver_id, pickup_area_code, 
                 total_amount, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (order_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at,
                    driver_id = EXCLUDED.driver_id
            """, fact_orders_data)
            logger.info(f"✓ Inserted {len(fact_orders_data)} orders")
        except Exception as e:
            logger.error(f"Error inserting orders: {e}")
            conn.rollback()
            raise

    # Insert into fact_routes
    if fact_routes_data:
        try:
            execute_batch(cur, """
                INSERT INTO fact_routes 
                (order_id, pickup_area, delivery_area, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (order_id, pickup_area, delivery_area) DO NOTHING
            """, fact_routes_data)
            logger.info(f"✓ Inserted {len(fact_routes_data)} routes")
        except Exception as e:
            logger.error(f"Error inserting routes: {e}")
            # Don't fail entire ETL for routes

    # Update area statistics
    if area_updates:
        for area_code, count in area_updates.items():
            try:
                cur.execute("""
                    INSERT INTO dim_areas (area_code, area_name, total_deliveries)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (area_code) DO UPDATE SET
                        total_deliveries = dim_areas.total_deliveries + EXCLUDED.total_deliveries,
                        last_updated = CURRENT_TIMESTAMP
                """, (area_code, f"Area {area_code}", count))
            except Exception as e:
                logger.error(f"Error updating area {area_code}: {e}")

        logger.info(f"✓ Updated {len(area_updates)} areas")

    conn.commit()
    cur.close()
    conn.close()

    logger.info("✓ Data loaded successfully!")

def run_etl_cycle():
    """Run one ETL cycle"""
    logger.info("=" * 50)
    logger.info("Starting ETL cycle...")

    try:
        # Extract from MinIO
        orders = extract_orders_from_minio()

        # Load to Postgres
        load_to_warehouse(orders)

        logger.info("ETL cycle completed!")

    except Exception as e:
        logger.error(f"ETL cycle failed: {e}", exc_info=True)


# =====================
# MAIN LOOP
# =====================
def wait_for_services():
    """Wait for Postgres and MinIO to be ready"""
    logger.info("Waiting for services to be ready...")

    max_retries = 30

    # Wait for Postgres
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            conn.close()
            logger.info("✓ Postgres is ready!")
            break
        except Exception as e:
            logger.warning(f"Postgres not ready (attempt {i + 1}/{max_retries})")
            time.sleep(2)
    else:
        raise Exception("Postgres not available")

    # Wait for MinIO
    for i in range(max_retries):
        try:
            client = get_minio_client()
            client.bucket_exists(MINIO_CONFIG["bucket"])
            logger.info("✓ MinIO is ready!")
            break
        except Exception as e:
            logger.warning(f"MinIO not ready (attempt {i + 1}/{max_retries})")
            time.sleep(2)
    else:
        raise Exception("MinIO not available")


def start_etl_worker():
    """Main ETL worker entry point"""
    logger.info("=" * 60)
    logger.info("ETL WORKER STARTING...")
    logger.info("=" * 60)

    try:
        # Wait for dependencies
        wait_for_services()

        # Initialize database
        init_database()

        # Run ETL loop
        logger.info(f"ETL will run every {PROCESSING_INTERVAL} seconds")

        while True:
            run_etl_cycle()
            logger.info(f"Sleeping for {PROCESSING_INTERVAL} seconds...")
            time.sleep(PROCESSING_INTERVAL)

    except KeyboardInterrupt:
        logger.info("ETL worker shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    start_etl_worker()