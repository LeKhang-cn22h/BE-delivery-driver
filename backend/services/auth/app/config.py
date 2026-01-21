from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ================= Redis =================
    REDIS_HOST: str
    REDIS_PORT: int

    # ================= RabbitMQ =================
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_QUEUE_NAME: str
    RABBITMQ_EXCHANGE_NAME: str
    RABBITMQ_ROUTING_KEY: str

    # ================= Kafka =================
    KAFKA_BOOTSTRAP_SERVERS: str

    # ================= Supabase =================
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # ================= Service =================
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 7000

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
