from fastapi import FastAPI
from presentation.api.dispatch_routes import router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Approve Order Service")

app.include_router(router)
