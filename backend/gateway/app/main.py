"""
API Gateway - Hệ thống Quản lý Vận tải
Main Entry Point - Centralized gateway cho tất cả microservices
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import sys

import logging
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
# Import middleware
from middleware.auth_middleware import AuthMiddleware, RoleCheckMiddleware

# Import routers
from routers import auth_proxy, receive_orders_proxy, routing_proxy, orders_proxy, tracking_proxy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        # Uncomment để log vào file
        # logging.FileHandler('gateway.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ===== CREATE FASTAPI APP =====

app = FastAPI(
    title="API Gateway - Hệ thống Vận tải",
    description="""
    Centralized API Gateway cho hệ thống quản lý vận chuyển
    
    ## Services
    - **Auth Service**: Authentication & Authorization
    - **Receive Orders Service**: Quản lý đơn hàng
    - **Transport Service**: Quản lý vận chuyển (coming soon)
    
    ## Authentication
    Hầu hết endpoints cần JWT token trong header:
```
    Authorization: Bearer <your_token>
```
    
    Get token bằng cách login qua `/api/v1/auth/login`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Support Team",
        "email": "support@transport.com"
    }
)

# ===== CORS MIDDLEWARE =====
# Phải thêm TRƯỚC auth middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== AUTH MIDDLEWARE =====
# Verify JWT token cho protected routes

app.add_middleware(
    AuthMiddleware,
    auth_service_url=os.getenv("AUTH_SERVICE_URL", "http://auth_service:7000")
)

# ===== ROLE CHECK MIDDLEWARE (Optional) =====
# Uncomment nếu cần role-based access control

ROLE_REQUIREMENTS = {
    # Admin-only endpoints
    "/api/v1/admin/*": ["admin"],
    
    # Dispatcher có thể assign orders
    "/api/v1/orders/assign": ["admin", "dispatcher"],
    
    # Chỉ drivers mới có thể update delivery status
    "/api/v1/orders/*/pickup": ["driver"],
    "/api/v1/orders/*/deliver": ["driver"],
}
# Auth router - Public + Protected endpoints
app.include_router(
    auth_proxy.router,
    tags=[" Authentication"]
)

# Orders router - Protected endpoints
app.include_router(
    receive_orders_proxy.router,
    tags=[" Orders Management"]
)
app.include_router(
    orders_proxy.routerP,
    tags=[" Post Offices"]
)
app.include_router(
    orders_proxy.routerD,
    tags=[" Drivers"]
)
app.include_router(
    routing_proxy.router,
    tags=[" Routing Service"]
)

app.include_router(
    tracking_proxy.router,
    tags=[" Driver Tracking Service"]
)

# TODO: Thêm router khác
# from routers import transport_proxy
# app.include_router(
#     transport_proxy.router,
#     tags=[" Transport Management"]
# )

# ===== ROOT ENDPOINTS =====
# Orders router - Protected endpoints
# Orders domain service (port 8002)
app.include_router(
    orders_proxy.router,
    tags=[" Orders Domain Service"]
)

@app.get("/", tags=["System"])
async def root():
    """
    Gateway root endpoint
    Hiển thị thông tin về available services và endpoints
    """
    return {
        "service": "API Gateway - Hệ thống Vận tải",
        "version": "1.0.0",
        "status": "running",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat(),
        
        "available_services": {
            "auth": {
                "base_url": "/api/v1/auth",
                "description": "Authentication & User Management",
                "endpoints": {
                    "public": [
                        "POST /api/v1/auth/register - Đăng ký",
                        "POST /api/v1/auth/login - Đăng nhập",
                        "POST /api/v1/auth/refresh - Làm mới token",
                        "POST /api/v1/auth/reset-password - Quên mật khẩu",
                    ],
                    "protected": [
                        "GET /api/v1/auth/me - Thông tin user",
                        "PATCH /api/v1/auth/me - Cập nhật profile",
                        "POST /api/v1/auth/logout - Đăng xuất",
                    ]
                }
            },
            
            "orders": {
                "base_url": "/api/v1/orders",
                "description": "Order Management System",
                "endpoints": {
                    "protected": [
                        "POST /api/v1/orders/ - Tạo đơn hàng",
                        "GET /api/v1/orders/pending - Danh sách pending",
                        "GET /api/v1/orders/{order_id} - Chi tiết đơn",
                        "PATCH /api/v1/orders/{order_id}/status - Cập nhật trạng thái",
                    ]
                }
            },
            
            "transport": {
                "base_url": "/api/v1/transport",
                "description": "Transport & Logistics (Coming soon)",
                "status": "planned"
            }
        },
        
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        
        "support": {
            "health_check": "/health",
            "email": "support@transport.com"
        }
    }


@app.get("/health", tags=["System"])
async def health_check():
    import httpx
    
    services_status = {}
    
    # List of backend services to check
    services = {
        "auth_service": os.getenv("AUTH_SERVICE_URL", "http://auth_service:7000"),
        "receive_orders_service": os.getenv("RECEIVE_ORDERS_SERVICE_URL", "http://receive_orders_service:8001"),
    }
    
    # Check each service
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, url in services.items():
            try:
                response = await client.get(f"{url}/health")
                services_status[name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": url,
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2)
                }
            except httpx.TimeoutException:
                services_status[name] = {
                    "status": "timeout",
                    "url": url,
                    "error": "Service did not respond in time"
                }
            except Exception as e:
                services_status[name] = {
                    "status": "unreachable",
                    "url": url,
                    "error": str(e)
                }
    
    # Overall health
    all_healthy = all(
        service["status"] == "healthy" 
        for service in services_status.values()
    )
    
    gateway_status = {
        "gateway": "healthy",
        "overall_status": "healthy" if all_healthy else "degraded",
        "services": services_status,
        "timestamp": datetime.now().isoformat()
    }
    
    # Return 503 if any service is down (optional)
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        content=gateway_status,
        status_code=status_code
    )
# ===== REQUEST/RESPONSE LOGGING MIDDLEWARE =====

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log tất cả requests và responses với process time
    """
    import time
    
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate process time
    process_time = time.time() - start_time
    
    # Log with color coding by status
    status_code = response.status_code
    if status_code < 400:
        log_level = logging.INFO
        emoji = "✓"
    elif status_code < 500:
        log_level = logging.WARNING
        emoji = "⚠"
    else:
        log_level = logging.ERROR
        emoji = "✗"
    
    logger.log(
        log_level,
        f"{emoji} {request.method} {request.url.path} "
        f"Status: {status_code} "
        f"Time: {process_time:.3f}s "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    # Add custom headers
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    response.headers["X-Gateway-Version"] = "1.0.0"
    
    return response


# ===== STARTUP & SHUTDOWN EVENTS =====

@app.on_event("startup")
async def startup_event():
    """
    Chạy khi Gateway khởi động
    """
    logger.info("=" * 70)
    logger.info(" API Gateway - Hệ thống Vận tải Starting...")
    logger.info("=" * 70)
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Auth Service: {os.getenv('AUTH_SERVICE_URL', 'http://auth_service:7000')}")
    logger.info(f"Orders Service: {os.getenv('RECEIVE_ORDERS_SERVICE_URL', 'http://receive_orders_service:8001')}")
    logger.info(f"CORS Origins: {os.getenv('CORS_ORIGINS', '*')}")
    logger.info("=" * 70)
    logger.info(" API Documentation: http://localhost:8000/docs")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Chạy khi Gateway tắt
    """
    logger.info("=" * 70)
    logger.info(" API Gateway Shutting down...")
    logger.info("=" * 70)


# ===== CUSTOM ERROR HANDLERS =====

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """
    Custom 404 handler
    """
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Endpoint not found",
            "path": request.url.path,
            "method": request.method,
            "hint": "Check /docs for available endpoints",
            "available_services": ["/api/v1/auth", "/api/v1/orders"]
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(
        "Internal server error on %s",
        request.url.path,
        exc_info=True
    )

    debug = os.getenv("ENVIRONMENT", "development") == "development"

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "hint": "Check logs or contact support",
            "service": "gateway"
        }
    )



@app.exception_handler(502)
async def bad_gateway_handler(request: Request, exc):
    """
    Custom 502 handler - Service unavailable
    """
    logger.error(f"Bad gateway on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=502,
        content={
            "detail": "Backend service unavailable",
            "hint": "The requested service is temporarily unavailable",
            "check": "/health for service status"
        }
    )
# ===== ADMIN ENDPOINTS (Optional) =====

@app.get("/metrics", tags=["Admin"], include_in_schema=False)
async def metrics():

    return {
        "requests_total": 0,
        "requests_per_service": {},
        "average_response_time": 0
    }