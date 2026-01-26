# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from presentation.api.order_routes import router as order_router
import uvicorn
import os

app = FastAPI(
    title="Order Management Microservice",
    description="Microservice quản lý đơn hàng - Khách hàng đặt hàng với nhiều kiện",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên chỉ định cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(order_router)

@app.get("/")
async def root():
    return {
        "service": "Order Management Microservice",
        "status": "running",
        "version": "1.0.0",
        "description": "Quản lý đơn hàng - 1 đơn nhiều kiện"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "order-management"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True  # Tắt trong production
    )

