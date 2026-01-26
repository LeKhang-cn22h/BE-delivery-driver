from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import routes
from core.config import settings

app = FastAPI(title=settings.APP_NAME)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(routes.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Routing Service API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8386, reload=True)