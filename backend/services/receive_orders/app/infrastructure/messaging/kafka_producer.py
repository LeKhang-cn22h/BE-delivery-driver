import json
import os
from confluent_kafka import Producer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9093")

producer = Producer({
    "bootstrap.servers": KAFKA_BOOTSTRAP
})

def send_event(topic: str, key: str, value: dict):
    producer.produce(
        topic=topic,
        key=key,
        value=json.dumps(value, ensure_ascii=False)
    )
    producer.flush()
