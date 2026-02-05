# main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from presentation.api.order_routes import order_router, get_event_publisher
from presentation.api.post_office.post_office_routes import post_office_router
from presentation.api.driver.driver_routes import driver_router
from presentation.api.pickup_schedule_routes import router as pickup_router

import uvicorn
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager
    - Startup: Initialize and start Kafka Event Publisher
    - Shutdown: Stop Kafka Event Publisher gracefully
    """
    # ========== STARTUP ==========
    logger.info("🚀 Starting Order Management Microservice...")

    try:
        # Initialize Kafka Event Publisher
        logger.info("Initializing Kafka Event Publisher...")
        event_publisher = await get_event_publisher()
        logger.info(f"✅ Kafka Event Publisher initialized: {event_publisher.bootstrap_servers}")

    except Exception as e:
        logger.error(f"❌ Failed to initialize Kafka Event Publisher: {e}")
        logger.warning("⚠️ Application will start but events will NOT be published to Kafka!")
        # Don't raise - allow app to start even if Kafka is down
        # This is useful for local development

    logger.info("✅ Application startup complete")

    yield

    # ========== SHUTDOWN ==========
    logger.info("🛑 Shutting down Order Management Microservice...")

    try:
        # Stop Kafka Event Publisher
        logger.info("Stopping Kafka Event Publisher...")
        event_publisher = await get_event_publisher()
        await event_publisher.stop()
        logger.info("✅ Kafka Event Publisher stopped")

    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

    logger.info("✅ Application shutdown complete")


# Create FastAPI app with lifecycle
app = FastAPI(
    title="Order Management Microservice",
    description="Microservice quản lý đơn hàng, cửa hàng - Khách hàng đặt hàng với nhiều kiện",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  # ← QUAN TRỌNG: Thêm lifespan
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
app.include_router(order_router)
app.include_router(post_office_router)
app.include_router(driver_router)
app.include_router(pickup_router)

@app.get("/")
async def root():
    return {
        "service": "Order Management Microservice",
        "status": "running",
        "version": "1.0.0",
        "description": "Quản lý đơn hàng, cửa hàng - Khách hàng đặt hàng với nhiều kiện"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "order-management"
    }


@app.get("/health/kafka")
async def health_kafka():
    """
    Kiểm tra trạng thái kết nối Kafka
    Endpoint này giúp debug xem Kafka producer có hoạt động không
    """
    try:
        event_publisher = await get_event_publisher()

        if event_publisher._started:
            return {
                "status": "healthy",
                "kafka": "connected",
                "bootstrap_servers": event_publisher.bootstrap_servers,
                "message": "Kafka producer is running and ready to publish events"
            }
        else:
            return {
                "status": "unhealthy",
                "kafka": "not_started",
                "message": "Event publisher exists but producer not started",
                "action": "Check application logs for startup errors"
            }

    except Exception as e:
        return {
            "status": "unhealthy",
            "kafka": "error",
            "error": str(e),
            "message": "Failed to get event publisher instance",
            "action": "Check if Kafka is running and accessible"
        }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True  # Tắt trong production
    )