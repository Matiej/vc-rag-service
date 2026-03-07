import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env.local"),
        env_file_encoding="utf-8",
    )

    app_env: str = "local"
    database_url: str
    pool_size: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
