import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from presentation.routes import router
from infrastructure.rabbitmq_client import RabbitMQClient
from application.consumers.order_consumer import OrderConsumer

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global RabbitMQ client
rabbitmq_client = RabbitMQClient()
order_consumer = OrderConsumer()


async def start_consuming():
    """Background task để consume messages từ RabbitMQ"""
    try:
        await rabbitmq_client.connect()
        logger.info("🎧 Starting to consume messages from RabbitMQ...")
        await rabbitmq_client.consume(order_consumer.process_order_message)
    except Exception as e:
        logger.error(f"❌ Consumer error: {e}")
        # Retry after 5 seconds
        await asyncio.sleep(5)
        await start_consuming()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    # Startup
    logger.info("🚀 Starting Receive Orders Service...")

    # Khởi động RabbitMQ consumer trong background
    consumer_task = asyncio.create_task(start_consuming())

    yield

    # Shutdown
    logger.info("🛑 Shutting down Receive Orders Service...")
    consumer_task.cancel()
    await rabbitmq_client.disconnect()


# Create FastAPI app
app = FastAPI(
    title="Receive Orders Service",
    description="Service nhận và xử lý đơn hàng từ RabbitMQ",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers (vẫn giữ HTTP endpoints cho testing/manual operations)
app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "Receive Orders Service",
        "status": "running",
        "version": "1.0.0",
        "rabbitmq": {
            "connected": rabbitmq_client.connection is not None,
            "queue": rabbitmq_client.queue_name
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "rabbitmq_connected": rabbitmq_client.connection is not None
    }