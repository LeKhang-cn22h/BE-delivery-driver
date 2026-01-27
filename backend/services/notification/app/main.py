# main.py
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from presentation.api.routes import router as notification_router
from infrastructure.database.supabase_client import SupabaseClient
from infrastructure.messaging.kafka_consumer import (
    NotificationKafkaConsumer,
    NotificationEventHandlers
)
from infrastructure.messaging.kafka_producer import NotificationKafkaProducer
from infrastructure.database.notification_repository_impl import (
    SupabaseNotificationRepository
)
from application.services.notification_service import NotificationService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Kafka consumer instance
kafka_consumer: NotificationKafkaConsumer = None
consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    logger.info("Starting Notification Service...")
    
    # Initialize Supabase
    try:
        SupabaseClient.initialize(
            url=os.getenv("SUPABASE_URL"),
            key=os.getenv("SUPABASE_KEY")
        )
        logger.info("Supabase initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {str(e)}")
    
    # Initialize Kafka
    global kafka_consumer, consumer_task
    try:
        # Kafka Producer
        kafka_producer = NotificationKafkaProducer()
        
        # Kafka Consumer
        topics = ["order.created", "order.status_changed", "delivery.status_changed"]
        kafka_consumer = NotificationKafkaConsumer(topics)
        
        # Setup event handlers
        repository = SupabaseNotificationRepository()
        notification_service = NotificationService(repository, kafka_producer)
        handlers = NotificationEventHandlers(notification_service)
        
        kafka_consumer.register_handler("order.created", handlers.handle_order_created)
        kafka_consumer.register_handler("order.status_changed", handlers.handle_order_status_changed)
        kafka_consumer.register_handler("delivery.status_changed", handlers.handle_delivery_status_changed)
        
        # Start consumer in background
        consumer_task = asyncio.create_task(kafka_consumer.start())
        logger.info("Kafka consumer started")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka: {str(e)}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Notification Service...")
    if kafka_consumer:
        kafka_consumer.stop()
    if consumer_task:
        consumer_task.cancel()
    SupabaseClient.close()


# Create FastAPI app
app = FastAPI(
    title="Notification Service",
    description="Service quản lý thông báo cho hệ thống BE-delivery-driver",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(notification_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Notification Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "notification_service"
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("SERVICE_PORT", 8003))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )