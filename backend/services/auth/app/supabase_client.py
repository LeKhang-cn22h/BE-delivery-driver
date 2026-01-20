
# File này tạo và quản lý connection tới Supabase
# Sử dụng Singleton pattern để tái sử dụng connection
# ============================================

from supabase import create_client, Client
from config import get_settings
import logging

logger = logging.getLogger(__name__)

# Biến global lưu Supabase client
_supabase_client: Client = None


def get_supabase_client() -> Client:
    """
    Lấy Supabase client (Singleton pattern)
    Returns:
        Client: Supabase client đã kết nối
    
    Cách dùng:
        client = get_supabase_client()
        result = client.auth.sign_in_with_password(...)
    """
    global _supabase_client
    
    if _supabase_client is None:
        settings = get_settings()
        
        logger.info(f"Initializing Supabase client for: {settings.SUPABASE_URL}")
        
        # Tạo client với Service Role Key
        # Service Role Key có quyền bypass RLS (Row Level Security)
        _supabase_client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
        )
        
        logger.info("Supabase client initialized successfully")
    
    return _supabase_client


def get_supabase_anon_client() -> Client:
    """
    Lấy Supabase client với Anon Key
    
    Dùng khi muốn thao tác với quyền của user thường
    (tuân thủ RLS policies)
    """
    settings = get_settings()
    
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_ANON_KEY
    )