"""
Supabase Database Client
"""
from supabase import create_client, Client
from app.infrastructure.config.settings import get_settings


class SupabaseClient:
    """Singleton Supabase client"""

    _instance: Client = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client instance"""
        if cls._instance is None:
            settings = get_settings()
            cls._instance = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return cls._instance

    @classmethod
    def reset_client(cls):
        """Reset client instance (useful for testing)"""
        cls._instance = None