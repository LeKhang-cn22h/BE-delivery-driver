"""
Scheduler Service - Main Application
FastAPI application with Genetic Algorithm optimization
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from infrastructure.config.settings import get_settings
from presentation.api.routes import schedule_routes

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup/shutdown events"""
    # Startup
    print("🚀 Scheduler Service starting up...")
    print(f"📊 GA Configuration:")
    print(f"   - Population Size: {settings.GA_POPULATION_SIZE}")
    print(f"   - Generations: {settings.GA_GENERATIONS}")
    print(f"   - Mutation Rate: {settings.GA_MUTATION_RATE}")
    print(f"   - Crossover Rate: {settings.GA_CROSSOVER_RATE}")
    print(f"🔗 Supabase URL: {settings.SUPABASE_URL}")

    yield

    # Shutdown
    print("👋 Scheduler Service shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Scheduler Service",
    description="Microservice for optimizing driver-order scheduling using Genetic Algorithm",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    schedule_routes.router,
    prefix=settings.API_PREFIX
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Scheduler Service",
        "version": "1.0.0",
        "status": "running",
        "optimization": "Genetic Algorithm",
        "endpoints": {
            "create_schedules": f"{settings.API_PREFIX}/schedules/create",
            "get_driver_schedules": f"{settings.API_PREFIX}/schedules/driver/{{driver_id}}",
            "update_schedule": f"{settings.API_PREFIX}/schedules/{{schedule_id}}",
            "delete_schedule": f"{settings.API_PREFIX}/schedules/{{schedule_id}}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "scheduler_service",
        "ga_enabled": True
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )