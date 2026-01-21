import json
import os
import sys
import time
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from minio import Minio
from minio.error import S3Error
from datetime import datetime
from io import BytesIO
import logging

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== CONFIG ==========
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9093")
TOPIC = os.getenv("KAFKA_TOPIC", "orders")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "datalake")

MAX_RETRIES = 10
RETRY_DELAY = 5


# ========== WAIT FOR SERVICES ==========
def wait_for_kafka(bootstrap_servers, max_retries=MAX_RETRIES):
    """Wait for Kafka to be ready"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to Kafka... (attempt {attempt + 1}/{max_retries})")
            test_consumer = KafkaConsumer(
                bootstrap_servers=bootstrap_servers,
                api_version_auto_timeout_ms=5000
            )
            test_consumer.close()
            logger.info("✅ Kafka is ready!")
            return True
        except KafkaError as e:
            logger.warning(f"Kafka not ready: {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                logger.error("❌ Failed to connect to Kafka after max retries")
                return False
    return False


def wait_for_minio(client, max_retries=MAX_RETRIES):
    """Wait for MinIO to be ready"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to MinIO... (attempt {attempt + 1}/{max_retries})")
            client.list_buckets()
            logger.info("✅ MinIO is ready!")
            return True
        except S3Error as e:
            logger.warning(f"MinIO not ready: {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                logger.error("❌ Failed to connect to MinIO after max retries")
                return False
    return False


# ========== CONNECT MINIO ==========
logger.info(f"Connecting to MinIO at {MINIO_ENDPOINT}")
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

if not wait_for_minio(minio_client):
    logger.error("Cannot proceed without MinIO")
    sys.exit(1)

# Create bucket if not exists
try:
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)
        logger.info(f"✅ Created bucket: {MINIO_BUCKET}")
    else:
        logger.info(f"✅ Bucket already exists: {MINIO_BUCKET}")
except S3Error as e:
    logger.error(f"❌ Failed to create/check bucket: {e}")
    sys.exit(1)

# ========== CONNECT KAFKA ==========
logger.info(f"Connecting to Kafka at {KAFKA_BOOTSTRAP}, topic: {TOPIC}")

if not wait_for_kafka(KAFKA_BOOTSTRAP):
    logger.error("Cannot proceed without Kafka")
    sys.exit(1)


def safe_deserializer(data):
    """Safely deserialize JSON, skip empty or invalid messages"""
    if not data:
        logger.warning("⚠️ Received empty message, skipping...")
        return None
    try:
        return json.loads(data.decode("utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON: {e}, Raw: {data[:100]}")
        return None
    except Exception as e:
        logger.error(f"❌ Deserializer error: {e}")
        return None


try:
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="datalake-writer",
        value_deserializer=safe_deserializer,
        # consumer_timeout_ms removed - will run indefinitely
        max_poll_interval_ms=300000,
        session_timeout_ms=30000,  # Increased from 10s to 30s
        heartbeat_interval_ms=3000,
        request_timeout_ms=40000  # Added timeout for requests
    )
    logger.info(f"✅ Connected to Kafka topic: {TOPIC}")
except KafkaError as e:
    logger.error(f"❌ Failed to create Kafka consumer: {e}")
    sys.exit(1)

# ========== MAIN LOOP ==========
logger.info("🚀 Kafka to DataLake service started...")
logger.info(f"📊 Consuming from topic: {TOPIC}")
logger.info(f"💾 Writing to bucket: {MINIO_BUCKET}")

message_count = 0

try:
    for msg in consumer:
        try:
            data = msg.value

            # Skip None/empty messages
            if data is None:
                continue

            message_count += 1

            # Generate file path with date partitioning
            now = datetime.utcnow()
            date_path = now.strftime("%Y/%m/%d")
            timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
            filename = f"orders/{date_path}/{timestamp}.json"

            # Prepare content
            content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

            # Upload to MinIO
            minio_client.put_object(
                MINIO_BUCKET,
                filename,
                data=BytesIO(content),
                length=len(content),
                content_type="application/json"
            )

            logger.info(f"✅ [{message_count}] Saved to DataLake: {filename} ({len(content)} bytes)")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse message: {e}")
            logger.error(f"Raw message: {msg.value}")
            continue

        except S3Error as e:
            logger.error(f"❌ Failed to write to MinIO: {e}")
            logger.error(f"Data: {data}")
            continue

        except Exception as e:
            logger.error(f"❌ Unexpected error processing message: {e}")
            continue

except KeyboardInterrupt:
    logger.info("🛑 Shutting down gracefully...")

except Exception as e:
    logger.error(f"❌ Fatal error: {e}")

finally:
    consumer.close()
    logger.info(f"✅ Service stopped. Total messages processed: {message_count}")