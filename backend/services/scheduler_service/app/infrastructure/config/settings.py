"""
Configuration settings for Scheduler Service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8003
    API_PREFIX: str = "/api/v1"

    # CORS Configuration
    ALLOWED_ORIGINS: list = ["*"]

    # Genetic Algorithm Parameters
    GA_POPULATION_SIZE: int = 100
    GA_GENERATIONS: int = 200
    GA_MUTATION_RATE: float = 0.1
    GA_CROSSOVER_RATE: float = 0.8
    GA_ELITE_SIZE: int = 10
    GA_TOURNAMENT_SIZE: int = 5

    # Scheduling Constraints
    MAX_ORDERS_PER_DRIVER: int = 15
    MAX_WORKING_HOURS: float = 8.0
    PRIORITY_WEIGHT: float = 0.3
    DISTANCE_WEIGHT: float = 0.4
    BALANCE_WEIGHT: float = 0.3

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()