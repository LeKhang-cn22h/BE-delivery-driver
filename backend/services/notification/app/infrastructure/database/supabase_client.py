# infrastructure/database/supabase_client.py
from supabase import create_client, Client
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase Client"""
    _instance: Optional[Client] = None
    _url: Optional[str] = None
    _key: Optional[str] = None

    @classmethod
    def initialize(cls, url: str, key: str) -> None:
        """Khởi tạo Supabase client với URL và Key"""
        cls._url = url
        cls._key = key
        cls._instance = None  # Reset instance để tạo lại với config mới

    @classmethod
    def get_client(cls) -> Client:
        """Lấy Supabase client instance"""
        if cls._instance is None:
            if cls._url is None or cls._key is None:
                # Lấy từ environment variables
                cls._url = os.getenv("SUPABASE_URL")
                cls._key = os.getenv("SUPABASE_KEY")
                
                if not cls._url or not cls._key:
                    raise ValueError(
                        "Supabase URL and Key must be provided. "
                        "Set SUPABASE_URL and SUPABASE_KEY environment variables "
                        "or call SupabaseClient.initialize(url, key)"
                    )
            
            logger.info(f"Connecting to Supabase at {cls._url}")
            cls._instance = create_client(cls._url, cls._key)
            logger.info("Supabase client connected successfully")
        
        return cls._instance

    @classmethod
    def close(cls) -> None:
        """Đóng connection (nếu cần)"""
        if cls._instance is not None:
            cls._instance = None
            logger.info("Supabase client connection closed")


# Helper function để test connection
async def test_connection() -> bool:
    """Test Supabase connection"""
    try:
        client = SupabaseClient.get_client()
        # Test bằng cách query một bảng đơn giản
        result = client.table('notifications').select("count", count="exact").limit(0).execute()
        logger.info("Supabase connection test successful")
        return True
    except Exception as e:
        logger.error(f"Supabase connection test failed: {str(e)}")
        return False