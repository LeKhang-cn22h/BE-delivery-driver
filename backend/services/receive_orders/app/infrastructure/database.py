import os
from supabase import create_client, Client

class Database:
    _client: Client = None

    @classmethod
    def get_client(cls, schema: str = "delivery") -> Client:
        if cls._client is None:
            cls._client = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )
        return cls._client.schema(schema)
