import datetime
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ws.location_routes import router as location_router
from ws.websocket_routes import router as websocket_router


# ================== FASTAPI APP ==================

app = FastAPI(
    title="Driver Tracking Service",
    description="Real-time GPS tracking và lưu lịch sử di chuyển của driver",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(location_router)
app.include_router(websocket_router)

@app.get("/", tags=["System"])
def root():
    return {"service": "Driver Tracking Service", "status": "running"}

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "service": "tracking", "timestamp": datetime.now().isoformat()}


@app.on_event("startup")
async def startup():
    print("=" * 50)
    print(" Driver Tracking Service Started")
    print(" Port: 8007")
    print("=" * 50)