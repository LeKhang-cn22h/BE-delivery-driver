"""
 FILE: http_client.py

 VAI TRÒ:
- Là lớp dùng chung trong API Gateway
- Phụ trách gửi HTTP request sang các microservice khác
- Giúp Gateway KHÔNG phụ thuộc trực tiếp vào thư viện httpx
- Dễ thay thế, mock, test
"""
# Thư viện HTTP async, rất phù hợp với FastAPI
import httpx
class HttpClient:
    """
     Lớp HttpClient
    - Đóng vai trò như một HTTP adapter
    - Gateway gọi service con thông qua lớp này
    """

    async def get(self, url: str):
        # Tạo HTTP client async (tự động đóng khi ra khỏi context)
        async with httpx.AsyncClient() as client:

            # Gửi request GET
            response = await client.get(url)

            # Parse response sang JSON
            return response.json()
