from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_EXPIRE_MINUTES: int = 60
    SEGMENTATION_MS_URL: str = "http://localhost:8000"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8001
    # C7: CORS origins are env-var driven so production URLs can be set without
    # touching source code. L1: narrow defaults to only the methods/headers used.
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": "../.env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
