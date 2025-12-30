"""
📌 VAI TRÒ:
- Là entry point của API Gateway
- Khởi tạo FastAPI app
- Đăng ký các router proxy để chuyển tiếp request
- KHÔNG chứa business logic
"""
from fastapi import FastAPI

# Import router chuyên proxy sang transport_service
from routers.transport_proxy import router

# Khởi tạo FastAPI application
app = FastAPI(
    title="API Gateway",
    description="Gateway chuyển tiếp request đến các microservices",
    version="1.0.0"
)

# Đăng ký router proxy
# prefix="/transport" → tất cả API transport đi qua:
# /transport/*
app.include_router(
    router,
    prefix="/transport",
    tags=["Transport Service"]
)
