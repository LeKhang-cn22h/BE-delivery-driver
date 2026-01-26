from supabase import create_client, Client
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class SupabaseClient:
    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            cls._instance = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")  
            )
        return cls._instance
