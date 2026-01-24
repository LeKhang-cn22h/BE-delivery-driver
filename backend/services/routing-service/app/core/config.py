from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    APP_NAME: str = "Routing Service"
    OSRM_BASE_URL: str = "http://osrm-server:5000"
    MAX_LOCATIONS: int = 100
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
SettingsInstance = Settings()