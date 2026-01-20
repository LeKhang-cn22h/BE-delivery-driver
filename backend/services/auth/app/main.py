# ============================================
# main.py - Entry point
# ============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Import router từ presentation layer
from presentation.api.routes import router as auth_router
from config import get_settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup và Shutdown events"""
    logger.info("Starting Auth Service...")
    settings = get_settings()
    logger.info(f"Supabase URL: {settings.SUPABASE_URL}")
    logger.info("Auth Service started!")
    
    yield
    
    logger.info("Shutting down Auth Service...")


app = FastAPI(
    title="Auth Service",
    description="Authentication Service với Supabase - Clean Architecture",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "service": "Auth Service",
        "version": "1.0.0",
        "architecture": "Clean Architecture",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}