import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class HTTPClient:
    """Shared HTTP client với retry logic và error handling"""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    async def request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[Any, Any]:
        """
        Generic request method
        """
        url = f"{self.base_url}{endpoint}"
        
        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=json_data,
                    params=params,
                    headers=default_headers
                )
                
                # Log request
                logger.info(
                    f"{method} {url} - Status: {response.status_code}"
                )
                
                # Raise for error status codes
                response.raise_for_status()
                
                return response.json()
                
        except httpx.TimeoutException:
            logger.error(f"Timeout calling {url}")
            raise HTTPException(
                status_code=504,
                detail=f"Service timeout: {self.base_url}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error calling {url}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {self.base_url}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling {url}: {e}")
            # Forward the error from downstream service
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.json() if e.response.content else str(e)
            )
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        return await self.request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, json_data: Dict) -> Dict:
        return await self.request("POST", endpoint, json_data=json_data)
    
    async def patch(self, endpoint: str, json_data: Dict) -> Dict:
        return await self.request("PATCH", endpoint, json_data=json_data)
    
    async def put(self, endpoint: str, json_data: Dict) -> Dict:
        return await self.request("PUT", endpoint, json_data=json_data)
    
    async def delete(self, endpoint: str) -> Dict:
        return await self.request("DELETE", endpoint)