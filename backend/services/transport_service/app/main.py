from fastapi import FastAPI
from presentation.api.route_controller import router

app = FastAPI(title="Transport Service")
app.include_router(router)
