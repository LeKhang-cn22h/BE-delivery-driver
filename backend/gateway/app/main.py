from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import routers
from routers import receive_orders_proxy

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="API Gateway",
    description="Gateway cho hệ thống quản lý vận chuyển",
    version="1.0.0"
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
app.include_router(receive_orders_proxy.router)



@app.get("/")
async def root():
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "status": "running",
        "available_services": {
            "receive_orders": "/api/v1/orders",
            "transport": "/api/v1/transport"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}