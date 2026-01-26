from pydantic_settings import BaseSettings
from pydantic import Field   

class Settings(BaseSettings):
    APP_NAME: str = "Routing Service"
    OSRM_BASE_URL: str = "http://osrm-server:5000"

    OSRM_TIMEOUT: int = Field(default=60)

    MAX_LOCATIONS: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
