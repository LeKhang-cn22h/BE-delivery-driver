import json
import os
import time
from datetime import datetime
from io import BytesIO
import logging

from minio import Minio
from minio.error import S3Error
import psycopg2
from psycopg2.extras import execute_values

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== CONFIG ==========
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "datalake")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres_warehouse")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "warehouse")
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin123")

PROCESSING_INTERVAL = int(os.getenv("PROCESSING_INTERVAL", "300"))  # 5 minutes

# ========== MINIO CLIENT ==========
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)


# ========== POSTGRES CONNECTION ==========
def get_postgres_connection():
    """Create PostgreSQL connection"""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


# ========== INIT DATABASE ==========
def init_database():
    """Create tables if not exist"""
    logger.info("Initializing database schema...")

    conn = get_postgres_connection()
    cur = conn.cursor()

    # Fact table: orders
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fact_orders (
            order_id VARCHAR(100) PRIMARY KEY,
            priority VARCHAR(50),
            customer_name VARCHAR(200),
            customer_phone VARCHAR(50),
            pickup_address TEXT,
            delivery_address TEXT,
            total_amount DECIMAL(15, 2),
            notes TEXT,
            num_items INT,
            created_at TIMESTAMP,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_source VARCHAR(100)
        );

        CREATE INDEX IF NOT EXISTS idx_orders_created_at ON fact_orders(created_at);
        CREATE INDEX IF NOT EXISTS idx_orders_customer_phone ON fact_orders(customer_phone);
    """)

    # Dimension table: order_items
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dim_order_items (
            id SERIAL PRIMARY KEY,
            order_id VARCHAR(100) REFERENCES fact_orders(order_id),
            item_name VARCHAR(200),
            item_qty INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_items_order_id ON dim_order_items(order_id);
    """)

    # Aggregated table: daily_metrics
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agg_daily_metrics (
            date DATE PRIMARY KEY,
            total_orders INT,
            total_revenue DECIMAL(15, 2),
            avg_order_value DECIMAL(15, 2),
            unique_customers INT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Processing log table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS etl_processing_log (
            id SERIAL PRIMARY KEY,
            file_path VARCHAR(500),
            status VARCHAR(50),
            records_processed INT,
            error_message TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

    logger.info("✅ Database schema initialized")


# ========== EXTRACT ==========
def extract_orders_from_minio(prefix="orders/"):
    """Extract all JSON files from MinIO"""
    logger.info(f"Extracting files from MinIO bucket: {MINIO_BUCKET}/{prefix}")

    orders = []
    file_paths = []

    try:
        objects = minio_client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=True)

        for obj in objects:
            if obj.object_name.endswith('.json'):
                try:
                    # Download file content
                    response = minio_client.get_object(MINIO_BUCKET, obj.object_name)
                    content = response.read()

                    # Parse JSON
                    order_data = json.loads(content)
                    orders.append(order_data)
                    file_paths.append(obj.object_name)

                    logger.info(f"✅ Extracted: {obj.object_name}")

                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error in {obj.object_name}: {e}")
                except Exception as e:
                    logger.error(f"❌ Error reading {obj.object_name}: {e}")

        logger.info(f"✅ Extracted {len(orders)} orders from MinIO")
        return orders, file_paths

    except S3Error as e:
        logger.error(f"❌ MinIO error: {e}")
        return [], []


# ========== TRANSFORM ==========
def transform_order(order):
    """Transform and clean order data"""
    try:
        # Extract basic fields
        transformed = {
            'order_id': order.get('order_id', ''),
            'priority': order.get('priority', 'normal'),
            'customer_name': order.get('customer_name', ''),
            'customer_phone': order.get('customer_phone', ''),
            'pickup_address': order.get('pickup_address', {}).get('address', ''),
            'delivery_address': order.get('delivery_address', {}).get('address', ''),
            'total_amount': float(order.get('total_amount', 0)),
            'notes': order.get('notes', ''),
            'num_items': len(order.get('items', [])),
            'created_at': order.get('created_at', datetime.now().isoformat()),
            'data_source': 'minio_datalake'
        }

        # Extract items
        items = []
        for item in order.get('items', []):
            items.append({
                'order_id': transformed['order_id'],
                'item_name': item.get('name', ''),
                'item_qty': int(item.get('qty', 0))
            })

        return transformed, items

    except Exception as e:
        logger.error(f"❌ Transform error: {e}, Order: {order}")
        return None, []


# ========== LOAD ==========
def load_orders_to_warehouse(orders_data):
    """Load transformed data to PostgreSQL"""
    logger.info(f"Loading {len(orders_data)} orders to warehouse...")

    conn = get_postgres_connection()
    cur = conn.cursor()

    success_count = 0
    error_count = 0

    for order_data, items_data in orders_data:
        try:
            # Insert order (use ON CONFLICT to avoid duplicates)
            cur.execute("""
                INSERT INTO fact_orders (
                    order_id, priority, customer_name, customer_phone,
                    pickup_address, delivery_address, total_amount, notes,
                    num_items, created_at, data_source
                ) VALUES (
                    %(order_id)s, %(priority)s, %(customer_name)s, %(customer_phone)s,
                    %(pickup_address)s, %(delivery_address)s, %(total_amount)s, %(notes)s,
                    %(num_items)s, %(created_at)s, %(data_source)s
                )
                ON CONFLICT (order_id) DO UPDATE SET
                    processed_at = CURRENT_TIMESTAMP
            """, order_data)

            # Insert items
            if items_data:
                items_values = [
                    (item['order_id'], item['item_name'], item['item_qty'])
                    for item in items_data
                ]
                execute_values(
                    cur,
                    "INSERT INTO dim_order_items (order_id, item_name, item_qty) VALUES %s",
                    items_values
                )

            success_count += 1

        except Exception as e:
            logger.error(f"❌ Load error for order {order_data.get('order_id')}: {e}")
            error_count += 1
            conn.rollback()
            continue

    # Commit all changes
    conn.commit()

    # Update daily metrics
    update_daily_metrics(cur)
    conn.commit()

    cur.close()
    conn.close()

    logger.info(f"✅ Loaded {success_count} orders, {error_count} errors")
    return success_count, error_count


def update_daily_metrics(cursor):
    """Update aggregated daily metrics"""
    logger.info("Updating daily metrics...")

    cursor.execute("""
        INSERT INTO agg_daily_metrics (date, total_orders, total_revenue, avg_order_value, unique_customers)
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as total_orders,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_order_value,
            COUNT(DISTINCT customer_phone) as unique_customers
        FROM fact_orders
        GROUP BY DATE(created_at)
        ON CONFLICT (date) DO UPDATE SET
            total_orders = EXCLUDED.total_orders,
            total_revenue = EXCLUDED.total_revenue,
            avg_order_value = EXCLUDED.avg_order_value,
            unique_customers = EXCLUDED.unique_customers,
            updated_at = CURRENT_TIMESTAMP
    """)

    logger.info("✅ Daily metrics updated")


# ========== MAIN ETL PIPELINE ==========
def run_etl_pipeline():
    """Main ETL pipeline"""
    logger.info("🚀 Starting ETL Pipeline...")

    try:
        # EXTRACT
        raw_orders, file_paths = extract_orders_from_minio()

        if not raw_orders:
            logger.info("No new data to process")
            return

        # TRANSFORM
        logger.info("Transforming data...")
        transformed_data = []

        for order in raw_orders:
            order_data, items_data = transform_order(order)
            if order_data:
                transformed_data.append((order_data, items_data))

        logger.info(f"✅ Transformed {len(transformed_data)} orders")

        # LOAD
        success_count, error_count = load_orders_to_warehouse(transformed_data)

        # Log processing
        conn = get_postgres_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO etl_processing_log (file_path, status, records_processed)
            VALUES (%s, %s, %s)
        """, (f"{len(file_paths)} files", "success", success_count))
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ ETL Pipeline completed: {success_count} success, {error_count} errors")

    except Exception as e:
        logger.error(f"❌ ETL Pipeline failed: {e}")


# ========== CONTINUOUS PROCESSING ==========
def run_continuous():
    """Run ETL pipeline continuously"""
    logger.info(f"🔄 Starting continuous ETL (interval: {PROCESSING_INTERVAL}s)")

    # Initialize database
    init_database()

    while True:
        try:
            run_etl_pipeline()
            logger.info(f"⏰ Waiting {PROCESSING_INTERVAL}s before next run...")
            time.sleep(PROCESSING_INTERVAL)
        except KeyboardInterrupt:
            logger.info("🛑 Stopping ETL processor...")
            break
        except Exception as e:
            logger.error(f"❌ Error in continuous loop: {e}")
            time.sleep(60)  # Wait 1 minute on error


# ========== ENTRY POINT ==========
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("ETL PROCESSOR SERVICE")
    logger.info("=" * 50)

    # Wait for services to be ready
    time.sleep(10)

    # Run continuous processing
    run_continuous()