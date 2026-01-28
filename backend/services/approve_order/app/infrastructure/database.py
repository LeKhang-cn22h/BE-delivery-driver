from supabase import create_client, Client
from typing import Optional
import os


class Database:
    """Database connection manager"""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls, schema: str = "delivery") -> Client:
        """
        Lấy Supabase client instance (Singleton pattern)

        Args:
            schema: Database schema name (default: "public")
        """
        if cls._instance is None:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")

            if not supabase_url or not supabase_key:
                raise ValueError(
                    "SUPABASE_URL và SUPABASE_KEY phải được set trong environment variables"
                )

            cls._instance = create_client(supabase_url, supabase_key)

        # Set schema cho client
        if schema != "delivery":
            cls._instance.schema(schema)

        return cls._instance

    @classmethod
    def close(cls):
        """Đóng connection"""
        cls._instance = None