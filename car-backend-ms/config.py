from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_EXPIRE_MINUTES: int = 60
    SEGMENTATION_MS_URL: str = "http://localhost:8000"
    STORAGE_BASE_PATH: str = "./storage"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8001

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
