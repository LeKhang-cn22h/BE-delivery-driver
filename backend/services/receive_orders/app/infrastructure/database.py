# app/infrastructure/database.py
from supabase import create_client
import os


class SupabaseClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._client = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
            )
            cls._instance = instance
        return cls._instance

    def get_client(self):
        return self._client
