"""
VAI TRÒ:
File này nằm trong tầng **API Gateway**.
Nhiệm vụ chính:
- Nhận request từ client (Web / Mobile / Postman)
- KHÔNG xử lý nghiệp vụ
- Chỉ chuyển tiếp (proxy / forward) request sang microservice Transport
- Trả kết quả từ Transport service về lại client
"""

from fastapi import APIRouter
from services.http_client import HttpClient

router = APIRouter()
client = HttpClient()

TRANSPORT_URL = "http://transport_service:8000"

@router.get("/optimize-route")
async def proxy():

    # Gửi request GET sang transport service
    # HttpClient.get là async → không block event loop
    response = await client.get(
        f"{TRANSPORT_URL}/optimize-route"
    )
    # Trả thẳng kết quả từ service con về client
    return response
