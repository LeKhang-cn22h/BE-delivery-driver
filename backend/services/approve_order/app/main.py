from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from presentation.api.routes import router as order_router
import uvicorn

# Tạo FastAPI app
app = FastAPI(
    title="Order Processing Service",
    description="API xử lý đơn hàng và phân vùng giao hàng",
    version="1.0.0"
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
    """Health check endpoint"""
    return {
        "message": "Order Processing Service is running",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check cho monitoring"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=4000,
        reload=True  # Tắt trong production
    )