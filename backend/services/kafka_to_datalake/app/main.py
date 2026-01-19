import json
import time
from datetime import datetime
from kafka import KafkaConsumer
import boto3

# ================== CONFIG ==================

KAFKA_BROKER = "kafka:9093"
KAFKA_TOPIC = "orders"
CONSUMER_GROUP = "datalake-writer"

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "admin123"
BUCKET_NAME = "datalake"

# ================== INIT KAFKA ==================

print("🚀 Connecting to Kafka...")

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id=CONSUMER_GROUP,
)

# ================== INIT MINIO ==================

print("🪣 Connecting to MinIO...")

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name="us-east-1",
)

# Tạo bucket nếu chưa có
try:
    s3.head_bucket(Bucket=BUCKET_NAME)
    print("✅ Bucket exists:", BUCKET_NAME)
except:
    print("📦 Creating bucket:", BUCKET_NAME)
    s3.create_bucket(Bucket=BUCKET_NAME)

# ================== CONSUME LOOP ==================

print("🔥 Kafka → DataLake consumer started...")

while True:
    try:
        for msg in consumer:
            event = msg.value

            # Partition theo thời gian
            now = datetime.utcnow()
            path = (
                f"orders/"
                f"year={now.year}/"
                f"month={now.month:02d}/"
                f"day={now.day:02d}/"
                f"hour={now.hour:02d}/"
            )

            filename = f"{path}{msg.topic}_{msg.partition}_{msg.offset}.json"

            body = json.dumps(event, ensure_ascii=False).encode("utf-8")

            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=filename,
                Body=body,
                ContentType="application/json",
            )

            print(f"✅ Saved: {filename}")

    except Exception as e:
        print("❌ Error:", e)
        time.sleep(5)
