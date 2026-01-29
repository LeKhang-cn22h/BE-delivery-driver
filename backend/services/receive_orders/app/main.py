from fastapi import FastAPI
from presentation.routes import router

app = FastAPI(title="Receive Orders Service")

app.include_router(router)
