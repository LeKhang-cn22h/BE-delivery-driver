import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from presentation.api.routes import router
from infrastructure.database.rabbitmq_client import RabbitMQClient

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rabbitmq_client = RabbitMQClient()


async def start_consuming():
    try:
        await rabbitmq_client.connect()
        await rabbitmq_client.consume()
    except Exception as e:
        logger.error(e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Manager Orders Service starting...")
    task = asyncio.create_task(start_consuming())
    yield
    task.cancel()
    await rabbitmq_client.disconnect()


app = FastAPI(
    title="Manager Orders Service",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)


@app.get("/")
def root():
    return {"service": "manager_orders", "status": "running"}
